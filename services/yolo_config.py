# YOLO 模型配置文件

import os

# YOLO 模型路径
YOLO_MODEL_PATH = os.environ.get('YOLO_MODEL_PATH', 'yolov8x.pt')

# YOLO 检测配置
YOLO_CONFIG = {
    # 置信度阈值
    'confidence_threshold': 0.5,

    # 检测间隔 (秒)
    'detection_interval': 0.5,

    # 使用的设备 ('cpu' 或 'cuda')
    'device': os.environ.get('YOLO_DEVICE', 'cpu'),

    # 模型大小选项: yolov8n, yolov8s, yolov8m, yolov8l, yolov8x
    # n: nano (最快)
    # s: small
    # m: medium
    # l: large
    # x: xlarge (最准确，当前使用)
    'model_size': 'x',

    # 重复报警间隔 (秒)
    'repeat_alarm_interval': 10,

    # 启用 YOLO 检测
    'enable_yolo': os.environ.get('ENABLE_YOLO', 'true').lower() == 'true',
}

# YOLO 类别映射到检测类型
DETECTION_CLASS_MAPPING = {
    'person': 'person',          # 人
    'bicycle': 'bicycle',        # 自行车
    'car': 'car',               # 汽车
    'dog': 'dog',               # 狗
    'cat': 'cat',               # 猫
    'bus': 'bus',               # 巴士
    'truck': 'truck',           # 卡车
    'phone': 'phone',           # 手机
    'laptop': 'laptop',         # 笔记本电脑
}

# COCO 数据集中的所有类别 (YOLOv8 默认检测类别)
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
    'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
    'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe',
    'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis',
    'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
    'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
    'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
    'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator',
    'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]
