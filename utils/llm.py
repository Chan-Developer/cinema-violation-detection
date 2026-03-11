import os
import json
import base64
import requests
from openai import OpenAI

def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if value is not None:
        value = value.strip()
    if value:
        return value
    raise RuntimeError(f"{name} 未配置，无法调用大模型")

def get_llm_provider():
    """获取配置的LLM提供商"""
    return os.environ.get('LLM_PROVIDER', 'modelscope')

def encode_image(image_path):
    """将图片编码为base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def encode_image_bytes(image_bytes):
    """将图片字节编码为base64"""
    return base64.b64encode(image_bytes).decode('utf-8')

def build_prompt(detections):
    """构建统一提示词，要求简洁、无表情、Markdown格式"""
    detection_text = "YOLO检测到的物体:\n"
    if detections:
        for d in detections:
            detection_text += f"- {d['class']}: 置信度 {d['confidence']:.2f}\n"
    else:
        detection_text += "- 未检测到明显物体\n"

    prompt = f"""你是影院行为监管员。请观察图片（含检测框）并结合检测结果输出**简短**分析。

【检测到的物体】
{detection_text}

要求：
1. 输出为 Markdown。
2. 不要使用任何表情符号。
3. 内容简洁，总字数不超过120字。
4. 使用以下固定结构（每行一条）：
# 影院行为监管员报告
- 抽烟行为：有/无（简述）
- 拍照/录视频：有/无（简述）
- 其他违规：有/无（简述）
结论：一句话建议
"""
    return prompt

def call_openai(detections, base64_image):
    """调用OpenAI API"""
    api_key = _require_env('OPENAI_API_KEY')
    client = OpenAI(api_key=api_key)
    prompt = build_prompt(detections)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
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
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=200
    )

    return response.choices[0].message.content

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
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
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
                        {"image": f"data:image/jpeg;base64,{base64_image}"}
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

    # 使用 OpenAI 兼容的 API
    client = OpenAI(
        base_url='https://api-inference.modelscope.cn/v1',
        api_key=api_key,
    )

    try:
        response = client.chat.completions.create(
            model='Qwen/Qwen3-VL-8B-Instruct',  # 更新为支持视觉的模型
            messages=[{
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': prompt,
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/jpeg;base64,{base64_image}',
                        },
                    }
                ],
            }],
            stream=False,
            max_tokens=200
        )

        return response.choices[0].message.content
    except Exception as e:
        # 不降级到本地分析，直接抛出给上层处理
        raise RuntimeError(f"ModelScope API 调用失败: {e}") from e


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
    elif provider == 'zhipu':
        return call_zhipu(detections, base64_image)
    elif provider == 'qwen':
        return call_qwen(detections, base64_image)
    elif provider == 'modelscope':
        return call_modelscope(detections, base64_image)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
