import os
import json
import base64
import requests
from openai import OpenAI

def get_llm_provider():
    """获取配置的LLM提供商"""
    return os.environ.get('LLM_PROVIDER', 'openai')

def encode_image(image_path):
    """将图片编码为base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def call_openai(detections, image_path):
    """调用OpenAI API"""
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    
    # 准备检测结果描述
    detection_text = "检测到的物体:\n"
    for d in detections:
        detection_text += f"- {d['class']}: 置信度 {d['confidence']:.2f}\n"
    
    # 编码图片
    base64_image = encode_image(image_path)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"你是一个图像分析助手。请根据以下YOLO检测结果和图片，描述图片中的内容。\n\n{detection_text}\n\n请用一段话描述图片内容，包括检测到的物体及其位置关系。"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=300
    )
    
    return response.choices[0].message.content

def call_zhipu(detections, image_path):
    """调用智谱AI API"""
    api_key = os.environ.get('ZHIPU_API_KEY')
    base64_image = encode_image(image_path)
    
    detection_text = "检测到的物体:\n"
    for d in detections:
        detection_text += f"- {d['class']}: 置信度 {d['confidence']:.2f}\n"
    
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
                    {"type": "text", "text": f"你是一个图像分析助手。请根据以下YOLO检测结果和图片，描述图片中的内容。\n\n{detection_text}\n\n请用一段话描述图片内容，包括检测到的物体及其位置关系。"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    return result['choices'][0]['message']['content']

def call_qwen(detections, image_path):
    """调用通义千问API (DashScope)"""
    api_key = os.environ.get('DASHSCOPE_API_KEY')
    base64_image = encode_image(image_path)

    detection_text = "检测到的物体:\n"
    for d in detections:
        detection_text += f"- {d['class']}: 置信度 {d['confidence']:.2f}\n"

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
                        {"text": f"你是一个图像分析助手。请根据以下YOLO检测结果和图片，描述图片中的内容。\n\n{detection_text}\n\n请用一段话描述图片内容，包括检测到的物体及其位置关系。"},
                        {"image": f"data:image/jpeg;base64,{base64_image}"}
                    ]
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    return result['output']['text']

def call_modelscope(detections, image_path):
    """调用ModelScope API (通义千问3.5-27B)"""
    api_key = os.environ.get('MODELSCOPE_API_KEY')

    # 如果没有API Key，返回基于检测结果的本地描述
    if not api_key:
        return generate_local_description(detections)

    # 准备检测结果描述
    detection_text = "检测到的物体:\n"
    if detections:
        for d in detections:
            detection_text += f"- {d['class']}: 置信度 {d['confidence']:.2f}\n"
    else:
        detection_text += "未检测到任何物体\n"

    # 使用base64编码的图片
    base64_image = encode_image(image_path)

    # 使用 OpenAI 兼容的 API
    client = OpenAI(
        base_url='https://api-inference.modelscope.cn/v1',
        api_key=api_key,
    )

    try:
        response = client.chat.completions.create(
            model='Qwen/Qwen3.5-27B',  # ModelScope Model-Id
            messages=[{
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': f'你是一个图像分析助手。请根据以下检测结果和图片，描述图片中的内容。\n\n{detection_text}\n\n请用一段话详细描述图片内容，包括检测到的物体及其位置关系。',
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
            max_tokens=300
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"ModelScope API 调用失败: {e}")
        # 失败时返回本地生成的描述
        return generate_local_description(detections)


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

def call_llm_api(detections, image_path):
    """统一调用LLM API"""
    provider = get_llm_provider()

    if provider == 'openai':
        return call_openai(detections, image_path)
    elif provider == 'zhipu':
        return call_zhipu(detections, image_path)
    elif provider == 'qwen':
        return call_qwen(detections, image_path)
    elif provider == 'modelscope':
        return call_modelscope(detections, image_path)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
