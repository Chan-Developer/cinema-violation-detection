# YOLO检测 + LLM识别

一个基于Flask的Web应用，结合YOLOv8目标检测和大语言模型进行图像理解和描述。

## 功能特点

- 🔍 YOLOv8 目标检测
- 🤖 大模型图像描述（支持OpenAI、智谱AI、通义千问）
- 📱 简洁的Web界面
- 🖼️ 图片上传和实时检测

## 环境要求

- Python 3.8+
- Node.js (可选，用于前端开发)

## 安装

1. 克隆项目并进入目录：
```bash
cd ~/project
```

2. 创建虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API Key
```

## 配置

编辑 `.env` 文件：

```env
# 选择LLM提供商: openai, zhipu, qwen
LLM_PROVIDER=openai

# OpenAI配置
OPENAI_API_KEY=your_openai_api_key

# 或智谱AI配置
ZHIPU_API_KEY=your_zhipu_api_key

# 或通义千问配置
DASHSCOPE_API_KEY=your_dashscope_api_key
```

## 运行

```bash
python app.py
```

服务将在 http://localhost:5000 启动。

## 使用

1. 打开浏览器访问 http://localhost:5000
2. 点击上传区域选择图片或拖拽图片
3. 点击"开始检测"按钮
4. 查看检测结果和LLM描述

## 项目结构

```
project/
├── app.py              # Flask主应用
├── requirements.txt    # Python依赖
├── .env.example       # 环境变量示例
├── README.md          # 说明文档
├── uploads/           # 上传的图片目录
├── templates/
│   └── index.html     # 前端页面
├── static/            # 静态文件
└── utils/
    ├── __init__.py
    └── llm.py         # LLM API调用
```

## API

### POST /detect

上传图片进行检测

**请求：**
- Content-Type: multipart/form-data
- Body: image (图片文件)

**响应：**
```json
{
  "success": true,
  "detections": [
    {"class": "person", "confidence": 0.95, "bbox": [x1, y1, x2, y2]},
    {"class": "dog", "confidence": 0.87, "bbox": [x1, y1, x2, y2]}
  ],
  "annotated_image": "base64编码的检测结果图",
  "llm_description": "LLM生成的图片描述"
}
```

## 依赖

- flask - Web框架
- ultralytics - YOLOv8
- openai - OpenAI API
- python-dotenv - 环境变量
- pillow - 图片处理
- requests - HTTP请求

## 注意事项

1. 首次运行时会自动下载YOLO模型
2. 确保API Key已正确配置
3. 大模型API会产生费用，请留意使用

## License

MIT
