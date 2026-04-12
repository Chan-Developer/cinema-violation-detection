import os
import json
import base64
import subprocess
import requests
from dotenv import dotenv_values


def _get_ark_client():
    try:
        from volcenginesdkarkruntime import Ark
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: volcenginesdkarkruntime. Run `pip install -r requirements.txt`."
        ) from exc
    return Ark


def _get_openai_client():
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: openai. Run `pip install -r requirements.txt`."
        ) from exc
    return OpenAI

def _require_env(name: str) -> str:
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    file_value = (dotenv_values(env_path).get(name) or '').strip()
    env_value = (os.environ.get(name) or '').strip()

    # LLM 密钥优先读取项目 .env，避免进程里残留旧环境变量导致鉴权失败
    if name in {
        'MODELSCOPE_API_KEY',
        'OPENAI_API_KEY',
        'DASHSCOPE_API_KEY',
        'ZHIPU_API_KEY',
        'ARK_API_KEY',
        'DOUBAO_API_KEY',
    }:
        value = file_value or env_value
    else:
        value = env_value or file_value

    if value is not None:
        value = value.strip()
    if value:
        return value
    raise RuntimeError(f"{name} 未配置，无法调用大模型")

def get_llm_provider():
    """获取配置的LLM提供商"""
    return _optional_env('LLM_PROVIDER', 'modelscope')


def _optional_env(name: str, default: str = '') -> str:
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    file_value = (dotenv_values(env_path).get(name) or '').strip()
    env_value = (os.environ.get(name) or '').strip()
    return env_value or file_value or default

def encode_image(image_path):
    """将图片编码为base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def encode_image_bytes(image_bytes):
    """将图片字节编码为base64"""
    return base64.b64encode(image_bytes).decode('utf-8')

def build_prompt(detections):
    """构建影院违规分析提示词，覆盖更常见的影院不文明行为"""
    detection_text = "YOLO检测到的物体:\n"
    if detections:
        for d in detections:
            detection_text += f"- {d['class']}: 置信度 {d['confidence']:.2f}\n"
    else:
        detection_text += "- 未检测到明显物体\n"

    prompt = f"""你是影院行为监管员。请根据影院监控画面和检测结果，判断是否存在影响观影秩序的违规或不文明行为。

重点关注这些影院常见问题：
- 抽烟、疑似电子烟、明显烟雾
- 拍照、录视频、举手机朝向银幕、手机屏幕长时间亮起影响他人
- 频繁走动、站立、挡住银幕、在过道停留
- 聚集、打闹、争执、大幅度动作影响他人观影
- 其他明显不文明行为（如吃味道重的食物、躺卧占座、脚踩座椅等）

判断原则：
- 证据明显再判“有”，拿不准时判“无”并写“不确定/证据不足”
- 不要因为单纯有人、单纯拿手机就直接判违规，要结合姿态、方向和场景
- 只根据当前画面判断，不要编造画面外的信息

【检测到的物体】
{detection_text}

要求：
1. 输出为 Markdown。
2. 不要使用任何表情符号。
3. 内容简洁，总字数不超过160字。
4. 使用以下固定结构（每行一条）：
# 影院行为监管员报告
- 抽烟行为：有/无（简述）
- 拍照/录视频：有/无（简述）
- 手机亮屏影响观影：有/无（简述）
- 走动/站立挡屏：有/无（简述）
- 聚集/打闹：有/无（简述）
- 其他违规：有/无（简述）
结论：一句话建议
"""
    return prompt


def _build_vision_data_url(base64_image, mime_type='image/jpeg'):
    return f"data:{mime_type};base64,{base64_image}"


def _build_chat_messages(prompt, base64_image):
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": _build_vision_data_url(base64_image)
                    }
                }
            ]
        }
    ]


def _build_ark_responses_input(prompt, base64_image):
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": prompt
                },
                {
                    "type": "input_image",
                    "image_url": _build_vision_data_url(base64_image)
                }
            ]
        }
    ]


def _extract_ark_response_text(response):
    output = getattr(response, 'output', None) or []
    texts = []

    for item in output:
        contents = getattr(item, 'content', None) or []
        for content in contents:
            if getattr(content, 'type', None) == 'output_text':
                text = getattr(content, 'text', None)
                if text:
                    texts.append(text)

    if texts:
        return "\n".join(texts).strip()

    output_text = getattr(response, 'output_text', None)
    if output_text:
        return output_text.strip()

    raise RuntimeError(f"Ark 响应中未找到文本内容: {response}")

def call_openai(detections, base64_image):
    """调用OpenAI API"""
    api_key = _require_env('OPENAI_API_KEY')
    OpenAI = _get_openai_client()
    client = OpenAI(api_key=api_key)
    prompt = build_prompt(detections)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=_build_chat_messages(prompt, base64_image),
        max_tokens=200
    )

    return response.choices[0].message.content


def call_doubao(detections, base64_image):
    """调用火山引擎豆包 / 方舟 SDK Responses API"""
    prompt = build_prompt(detections)
    api_key = _optional_env('ARK_API_KEY') or _optional_env('DOUBAO_API_KEY')
    if not api_key:
        api_key = _require_env('ARK_API_KEY')

    Ark = _get_ark_client()
    client = Ark(
        api_key=api_key,
        base_url=_optional_env('ARK_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3'),
    )

    model = _optional_env('ARK_MODEL', 'doubao-seed-1-8-251228')

    response = client.responses.create(
        model=model,
        input=_build_ark_responses_input(prompt, base64_image),
        max_output_tokens=320,
        thinking={"type": "disabled"},
    )

    return _extract_ark_response_text(response)

def call_zhipu(detections, base64_image):
    """调用智谱AI API"""
    api_key = _require_env('ZHIPU_API_KEY')
    prompt = build_prompt(detections)

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "glm-4v",
        "messages": _build_chat_messages(prompt, base64_image)
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    return result['choices'][0]['message']['content']

def call_qwen(detections, base64_image):
    """调用通义千问API (DashScope)"""
    api_key = _require_env('DASHSCOPE_API_KEY')
    prompt = build_prompt(detections)

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "qwen-vl-plus",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        },
                        {"image": _build_vision_data_url(base64_image)}
                    ]
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    return result['output']['text']

def call_modelscope(detections, base64_image):
    """调用ModelScope API (Qwen3-VL) - 分析标注图片"""
    api_key = _require_env('MODELSCOPE_API_KEY')
    prompt = build_prompt(detections)
    # 使用 HTTP 直连，避免某些环境下 openai/httpx 连接异常
    url = "https://api-inference.modelscope.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "Qwen/Qwen3-VL-8B-Instruct",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": _build_vision_data_url(base64_image)}},
            ],
        }],
        "stream": False,
        "max_tokens": 200,
    }

    def _extract_content(result_obj):
        try:
            return result_obj["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"ModelScope API 响应解析失败: {result_obj}") from e

    # 首选 Python HTTP 客户端
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        result = response.json()
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code} - {result}")
        return _extract_content(result)
    except Exception as first_error:
        # 某些环境下 Python TLS 与网关握手不稳定，回退到 curl 通道
        payload_text = json.dumps(payload, ensure_ascii=False)
        cmd = [
            "curl", "-sS", "-X", "POST", url,
            "-H", f"Authorization: Bearer {api_key}",
            "-H", "Content-Type: application/json",
            "--data-binary", "@-",
        ]
        try:
            proc = subprocess.run(
                cmd,
                input=payload_text,
                text=True,
                capture_output=True,
                timeout=70,
                check=False,
            )
        except Exception as curl_error:
            raise RuntimeError(
                f"ModelScope API 调用失败: python={first_error}; curl={curl_error}"
            ) from curl_error

        if proc.returncode != 0:
            raise RuntimeError(
                f"ModelScope API 调用失败: python={first_error}; curl={proc.stderr.strip()}"
            )

        try:
            curl_result = json.loads(proc.stdout or "{}")
        except Exception as parse_error:
            raise RuntimeError(
                f"ModelScope API 响应解析失败: {proc.stdout[:500]}"
            ) from parse_error

        if "error" in curl_result:
            raise RuntimeError(f"ModelScope API 调用失败: {curl_result['error']}")

        return _extract_content(curl_result)


def generate_local_description(detections):
    """本地生成图片描述（当LLM API不可用时）"""
    if not detections:
        return "图片中没有检测到任何物体。"

    # 统计物体类别
    classes = {}
    for d in detections:
        cls = d.get('class', 'unknown')
        classes[cls] = classes.get(cls, 0) + 1

    # 构建描述
    desc_parts = []
    for cls, count in classes.items():
        if count == 1:
            desc_parts.append(f"一个{cls}")
        else:
            desc_parts.append(f"{count}个{cls}")

    return f"图片中检测到{', '.join(desc_parts)}。"


def generate_local_analysis(detections):
    """
    本地生成分析描述（当LLM API不可用时）
    基于检测结果进行规则判断，不使用硬编码模板
    """
    if not detections:
        return "未检测到任何物体。"

    # 分析检测结果
    analysis = []
    has_person = False
    has_phone = False
    has_smoke = False

    for d in detections:
        cls = d.get('class', '').lower()
        conf = d.get('confidence', 0)

        if 'person' in cls:
            has_person = True
            analysis.append(f"检测到人物（置信度{conf:.0%}）")
        elif 'phone' in cls or 'mobile' in cls:
            has_phone = True
            analysis.append(f"检测到手机/相机（置信度{conf:.0%}） - 可能在拍照")
        elif 'smoke' in cls or 'cigarette' in cls:
            has_smoke = True
            analysis.append(f"检测到烟雾/香烟（置信度{conf:.0%}） - 可能在吸烟")
        else:
            analysis.append(f"检测到{cls}（置信度{conf:.0%}）")

    result = "检测分析：" + "；".join(analysis) + "。"

    # 判断违规
    violations = []
    if has_phone and has_person:
        violations.append("拍照/录视频")
    if has_smoke:
        violations.append("吸烟")

    if violations:
        result += "检测到以下违规行为：" + "、".join(violations) + "。"
    else:
        result += "未检测到明显违规行为。"

    return result

def call_llm_api(detections, base64_image):
    """统一调用LLM API - 分析标注图片并返回违规行为分析"""
    provider = get_llm_provider()

    if provider == 'openai':
        return call_openai(detections, base64_image)
    elif provider in {'doubao', 'ark', 'volcengine'}:
        return call_doubao(detections, base64_image)
    elif provider == 'zhipu':
        return call_zhipu(detections, base64_image)
    elif provider == 'qwen':
        return call_qwen(detections, base64_image)
    elif provider == 'modelscope':
        return call_modelscope(detections, base64_image)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
