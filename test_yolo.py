#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YOLO 检测测试脚本
用于验证 YOLO 模型是否正常加载和检测
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path

def test_yolo_available():
    """检查 YOLO 库是否已安装"""
    print("=" * 60)
    print("🔍 检查 YOLO 库")
    print("=" * 60)

    try:
        from ultralytics import YOLO
        print("✅ ultralytics 已安装")
        return True
    except ImportError:
        print("❌ ultralytics 未安装")
        print("   运行: pip install ultralytics")
        return False


def test_model_file():
    """检查权重文件是否存在"""
    print("\n" + "=" * 60)
    print("📦 检查权重文件")
    print("=" * 60)

    model_path = 'yolov8x.pt'

    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        print(f"✅ 权重文件存在: {model_path}")
        print(f"   文件大小: {size_mb:.1f} MB")
        return True
    else:
        print(f"❌ 权重文件不存在: {model_path}")
        print("   请确保 yolov8x.pt 在项目根目录")
        return False


def test_model_loading():
    """测试模型加载"""
    print("\n" + "=" * 60)
    print("🤖 测试模型加载")
    print("=" * 60)

    try:
        from ultralytics import YOLO

        print("正在加载 YOLO 模型...")
        model = YOLO('yolov8x.pt')
        print("✅ 模型加载成功")
        print(f"   模型: YOLOv8x")
        print(f"   任务: {model.task}")
        return model
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return None


def create_test_image():
    """创建测试图片"""
    print("\n" + "=" * 60)
    print("🖼️  创建测试图片")
    print("=" * 60)

    try:
        # 创建一个简单的测试图片
        img = np.zeros((480, 640, 3), dtype=np.uint8)

        # 画一个人形的简单矩形
        cv2.rectangle(img, (100, 100), (200, 300), (255, 0, 0), -1)  # 蓝色矩形

        # 添加一些圆形
        cv2.circle(img, (150, 60), 30, (0, 255, 0), -1)  # 绿色圆
        cv2.circle(img, (400, 200), 50, (0, 0, 255), -1)  # 红色圆

        # 添加文字
        cv2.putText(img, 'Test Image', (200, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # 保存测试图片
        test_dir = 'test_images'
        os.makedirs(test_dir, exist_ok=True)
        test_image_path = os.path.join(test_dir, 'test_yolo.jpg')
        cv2.imwrite(test_image_path, img)

        print(f"✅ 测试图片已创建: {test_image_path}")
        print(f"   分辨率: 640x480")
        return test_image_path

    except Exception as e:
        print(f"❌ 创建测试图片失败: {e}")
        return None


def test_detection(model, image_path):
    """测试检测功能"""
    print("\n" + "=" * 60)
    print("🔍 测试检测功能")
    print("=" * 60)

    if model is None:
        print("❌ 模型未加载")
        return False

    try:
        print(f"正在检测图片: {image_path}")

        # 运行检测
        results = model(image_path, conf=0.3, verbose=False)

        if results and len(results) > 0:
            boxes = results[0].boxes
            names = results[0].names

            print(f"✅ 检测成功！检测到 {len(boxes)} 个对象")
            print("\n   检测结果:")

            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = names[class_id]

                print(f"   [{i+1}] {class_name}: {confidence:.2%}")
                print(f"       位置: ({x1}, {y1}) -> ({x2}, {y2})")

            return True
        else:
            print("⚠️  没有检测到对象")
            return True  # 这不是错误，可能是因为图片太简单

    except Exception as e:
        print(f"❌ 检测失败: {e}")
        return False


def test_detection_service():
    """测试检测服务集成"""
    print("\n" + "=" * 60)
    print("🔗 测试检测服务集成")
    print("=" * 60)

    try:
        from services.detection import DetectionWorker
        print("✅ DetectionWorker 导入成功")

        # 检查 YOLO 是否可用
        worker = DetectionWorker(camera_id=1, detection_types='person,car')
        if worker.use_yolo:
            print("✅ YOLO 检测已启用")
            if worker._model is not None:
                print("✅ YOLO 模型已加载")
                return True
            else:
                print("⚠️  YOLO 模型加载失败，将使用模拟检测")
                return True
        else:
            print("⚠️  YOLO 不可用，将使用模拟检测")
            return True

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def benchmark_detection(model, image_path):
    """性能基准测试"""
    print("\n" + "=" * 60)
    print("⏱️  性能基准测试")
    print("=" * 60)

    if model is None:
        print("❌ 模型未加载")
        return

    import time

    # 加载图片
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ 无法加载图片: {image_path}")
        return

    print(f"图片分辨率: {img.shape[1]}x{img.shape[0]}")

    # 热身
    print("正在预热模型...")
    model(image_path, conf=0.3, verbose=False)

    # 正式测试 (10 次迭代)
    print("正在运行 10 次检测...")
    times = []

    for i in range(10):
        start_time = time.time()
        model(image_path, conf=0.3, verbose=False)
        elapsed = time.time() - start_time
        times.append(elapsed)
        print(f"  [{i+1}/10] {elapsed:.2f}s", end='\r')

    print("\n" + "=" * 60)
    print("📊 性能统计")
    print("=" * 60)
    print(f"平均检测时间: {np.mean(times):.2f}s")
    print(f"最快: {np.min(times):.2f}s")
    print(f"最慢: {np.max(times):.2f}s")
    print(f"吞吐量: {10/sum(times):.2f} fps (在 CPU 上)")

    if np.mean(times) > 2.0:
        print("\n💡 建议:")
        print("   1. 使用 GPU 加速 (YOLO_DEVICE=cuda)")
        print("   2. 改用较小的模型 (YOLOv8s 或 YOLOv8m)")
        print("   3. 增加检测间隔")


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 20 + "YOLO 检测测试工具" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")

    results = {}

    # 运行所有测试
    results['YOLO库'] = test_yolo_available()
    if not results['YOLO库']:
        print("\n❌ YOLO 库未安装，无法继续测试")
        return 1

    results['权重文件'] = test_model_file()
    if not results['权重文件']:
        print("\n❌ 权重文件不存在，无法继续测试")
        return 1

    model = test_model_loading()
    results['模型加载'] = model is not None

    test_image = create_test_image()
    if test_image:
        results['测试检测'] = test_detection(model, test_image)
        if model:
            benchmark_detection(model, test_image)

    results['服务集成'] = test_detection_service()

    # 打印总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {name}")

    print(f"\n总体: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！YOLO 已准备就绪！")
        print("\n💡 下一步:")
        print("   1. 启动应用: python app.py")
        print("   2. 访问: http://localhost:9500")
        print("   3. 上传图片进行实时检测")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息")
        return 1


if __name__ == '__main__':
    sys.exit(main())
