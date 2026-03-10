import os
import json
import base64
import requests
from openai import OpenAI

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

def call_openai(detections, base64_image):
    """调用OpenAI API"""
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    # 准备检测结果描述
    detection_text = "YOLO检测到的物体:\n"
    if detections:
        for d in detections:
            detection_text += f"- {d['class']}: 置信度 {d['confidence']:.2f}\n"
    else:
        detection_text += "- 未检测到明显物体\n"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""你是一个严格的影院行为监管员。请仔细观察这张图片。图片上有绿色检测框标注了检测到的人物。

【检测到的物体】
{detection_text}

请基于图片内容，逐人进行详细分析。特别关注以下违规行为：

【第一步：逐人分析违规行为】
对图片中每一个被标记的人物，必须逐一检查以下内容：

1️⃣ **抽烟行为检查（最重要）**：
   - 仔细观察是否看到香烟、烟雾、烟灰
   - 检查人物嘴部、手部是否有烟草制品
   - 是否可以看到烟雾轨迹或抽烟的姿态
   - 即使看不清楚，如果有烟雾迹象，也要标注为"可能在抽烟"

2️⃣ **拍照/录视频行为检查**：
   - 是否举着手机、相机或其他录制设备
   - 手机是否对准屏幕
   - 是否有自拍或录视频的姿态

3️⃣ **其他违规行为**：
   - 是否大声喧哗、过度活跃
   - 是否躺卧或不当坐姿
   - 是否有脚踩座位等不文明行为

【第二步：汇总违规统计】
- 总共检测到多少人
- 其中有多少人存在违规行为
- 具体列举每个人的违规行为（如"第1个人：正在抽烟"）
- 严重程度评级：
  * 🔴 严重：发现明确抽烟、大量烟雾
  * 🟠 中等：发现拍照/录视频、可疑抽烟迹象
  * 🟡 轻微：发现其他不文明行为

【输出要求】
请给出清晰的分析结果，格式如下：
- 场景：[描述影院环境]
- 人数：[总人数] 人，其中 [违规人数] 人违规
- 违规详情：[逐一列出每个人的违规行为]
- 最严重的违规：[指出最严重的违规行为是什么]
- 安全建议：[根据违规情况提出应对措施]"""
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
        max_tokens=600
    )

    return response.choices[0].message.content

def call_zhipu(detections, base64_image):
    """调用智谱AI API"""
    api_key = os.environ.get('ZHIPU_API_KEY')

    detection_text = "YOLO检测到的物体:\n"
    if detections:
        for d in detections:
            detection_text += f"- {d['class']}: 置信度 {d['confidence']:.2f}\n"
    else:
        detection_text += "- 未检测到明显物体\n"

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
                        "text": f"""你是一个严格的影院行为监管员。请仔细观察这张图片。图片上有绿色检测框标注了检测到的人物。

【检测到的物体】
{detection_text}

请基于图片内容，逐人进行详细分析。特别关注以下违规行为：

【第一步：逐人分析违规行为】
对图片中每一个被标记的人物，必须逐一检查以下内容：

1️⃣ **抽烟行为检查（最重要）**：
   - 仔细观察是否看到香烟、烟雾、烟灰
   - 检查人物嘴部、手部是否有烟草制品
   - 是否可以看到烟雾轨迹或抽烟的姿态
   - 即使看不清楚，如果有烟雾迹象，也要标注为"可能在抽烟"

2️⃣ **拍照/录视频行为检查**：
   - 是否举着手机、相机或其他录制设备
   - 手机是否对准屏幕
   - 是否有自拍或录视频的姿态

3️⃣ **其他违规行为**：
   - 是否大声喧哗、过度活跃
   - 是否躺卧或不当坐姿
   - 是否有脚踩座位等不文明行为

【第二步：汇总违规统计】
- 总共检测到多少人
- 其中有多少人存在违规行为
- 具体列举每个人的违规行为（如"第1个人：正在抽烟"）
- 严重程度评级：
  * 🔴 严重：发现明确抽烟、大量烟雾
  * 🟠 中等：发现拍照/录视频、可疑抽烟迹象
  * 🟡 轻微：发现其他不文明行为

【输出要求】
请给出清晰的分析结果，格式如下：
- 场景：[描述影院环境]
- 人数：[总人数] 人，其中 [违规人数] 人违规
- 违规详情：[逐一列出每个人的违规行为]
- 最严重的违规：[指出最严重的违规行为是什么]
- 安全建议：[根据违规情况提出应对措施]"""
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
    api_key = os.environ.get('DASHSCOPE_API_KEY')

    detection_text = "YOLO检测到的物体:\n"
    if detections:
        for d in detections:
            detection_text += f"- {d['class']}: 置信度 {d['confidence']:.2f}\n"
    else:
        detection_text += "- 未检测到明显物体\n"

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
                            "text": f"""你是一个严格的影院行为监管员。请仔细观察这张图片。图片上有绿色检测框标注了检测到的人物。

【检测到的物体】
{detection_text}

请基于图片内容，逐人进行详细分析。特别关注以下违规行为：

【第一步：逐人分析违规行为】
对图片中每一个被标记的人物，必须逐一检查以下内容：

1️⃣ **抽烟行为检查（最重要）**：
   - 仔细观察是否看到香烟、烟雾、烟灰
   - 检查人物嘴部、手部是否有烟草制品
   - 是否可以看到烟雾轨迹或抽烟的姿态
   - 即使看不清楚，如果有烟雾迹象，也要标注为"可能在抽烟"

2️⃣ **拍照/录视频行为检查**：
   - 是否举着手机、相机或其他录制设备
   - 手机是否对准屏幕
   - 是否有自拍或录视频的姿态

3️⃣ **其他违规行为**：
   - 是否大声喧哗、过度活跃
   - 是否躺卧或不当坐姿
   - 是否有脚踩座位等不文明行为

【第二步：汇总违规统计】
- 总共检测到多少人
- 其中有多少人存在违规行为
- 具体列举每个人的违规行为（如"第1个人：正在抽烟"）
- 严重程度评级：
  * 🔴 严重：发现明确抽烟、大量烟雾
  * 🟠 中等：发现拍照/录视频、可疑抽烟迹象
  * 🟡 轻微：发现其他不文明行为

【输出要求】
请给出清晰的分析结果，格式如下：
- 场景：[描述影院环境]
- 人数：[总人数] 人，其中 [违规人数] 人违规
- 违规详情：[逐一列出每个人的违规行为]
- 最严重的违规：[指出最严重的违规行为是什么]
- 安全建议：[根据违规情况提出应对措施]"""
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
    api_key = os.environ.get('MODELSCOPE_API_KEY')

    # 如果没有API Key，返回本地分析结果
    if not api_key:
        print("⚠️  ModelScope API Key 未配置，使用本地分析")
        return generate_local_analysis(detections)

    # 准备检测结果描述
    detection_text = "YOLO检测到的物体:\n"
    if detections:
        for d in detections:
            detection_text += f"- {d['class']}: 置信度 {d['confidence']:.2f}\n"
    else:
        detection_text += "- 未检测到明显物体\n"

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
                        'text': f"""你是一个严格的影院行为监管员。请仔细观察这张图片。图片上有绿色检测框标注了检测到的人物。

【检测到的物体】
{detection_text}

请基于图片内容，逐人进行详细分析。特别关注以下违规行为：

【第一步：逐人分析违规行为】
对图片中每一个被标记的人物，必须逐一检查以下内容：

1️⃣ **抽烟行为检查（最重要）**：
   - 仔细观察是否看到香烟、烟雾、烟灰
   - 检查人物嘴部、手部是否有烟草制品
   - 是否可以看到烟雾轨迹或抽烟的姿态
   - 即使看不清楚，如果有烟雾迹象，也要标注为"可能在抽烟"

2️⃣ **拍照/录视频行为检查**：
   - 是否举着手机、相机或其他录制设备
   - 手机是否对准屏幕
   - 是否有自拍或录视频的姿态

3️⃣ **其他违规行为**：
   - 是否大声喧哗、过度活跃
   - 是否躺卧或不当坐姿
   - 是否有脚踩座位等不文明行为

【第二步：汇总违规统计】
- 总共检测到多少人
- 其中有多少人存在违规行为
- 具体列举每个人的违规行为（如"第1个人：正在抽烟"）
- 严重程度评级：
  * 🔴 严重：发现明确抽烟、大量烟雾
  * 🟠 中等：发现拍照/录视频、可疑抽烟迹象
  * 🟡 轻微：发现其他不文明行为

【输出要求】
请给出清晰的分析结果，格式如下：
- 场景：[描述影院环境]
- 人数：[总人数] 人，其中 [违规人数] 人违规
- 违规详情：[逐一列出每个人的违规行为]
- 最严重的违规：[指出最严重的违规行为是什么]
- 安全建议：[根据违规情况提出应对措施]""",
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
            max_tokens=800
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ ModelScope API 调用失败: {e}")
        import traceback
        traceback.print_exc()
        # 失败时返回本地分析结果
        return generate_local_analysis(detections)


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
