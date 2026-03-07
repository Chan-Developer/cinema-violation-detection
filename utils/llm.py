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
    """调用通义千问API"""
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

def call_llm_api(detections, image_path):
    """统一调用LLM API"""
    provider = get_llm_provider()
    
    if provider == 'openai':
        return call_openai(detections, image_path)
    elif provider == 'zhipu':
        return call_zhipu(detections, image_path)
    elif provider == 'qwen':
        return call_qwen(detections, image_path)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
