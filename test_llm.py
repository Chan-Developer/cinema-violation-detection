#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ModelScope LLM 测试脚本
用于测试 ModelScope API 连接和功能
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_api_key():
    """检查 API Key 是否配置"""
    print("=" * 50)
    print("🔍 检查 API Key 配置")
    print("=" * 50)

    api_key = os.environ.get('MODELSCOPE_API_KEY')
    if api_key:
        print("✅ MODELSCOPE_API_KEY 已设置")
        print(f"   Token: {api_key[:20]}...{api_key[-10:]}")
        return True
    else:
        print("❌ MODELSCOPE_API_KEY 未设置")
        print("   请编辑 .env 文件并设置 MODELSCOPE_API_KEY")
        return False


def test_imports():
    """检查依赖是否已安装"""
    print("\n" + "=" * 50)
    print("📦 检查依赖")
    print("=" * 50)

    try:
        from openai import OpenAI
        print("✅ openai 已安装")
    except ImportError:
        print("❌ openai 未安装")
        print("   运行: pip install openai")
        return False

    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv 已安装")
    except ImportError:
        print("❌ python-dotenv 未安装")
        print("   运行: pip install python-dotenv")
        return False

    try:
        from PIL import Image
        print("✅ pillow 已安装")
    except ImportError:
        print("⚠️  pillow 未安装（可选）")

    return True


def test_connection():
    """测试 ModelScope API 连接"""
    print("\n" + "=" * 50)
    print("🌐 测试 ModelScope 连接")
    print("=" * 50)

    try:
        from openai import OpenAI

        api_key = os.environ.get('MODELSCOPE_API_KEY')
        client = OpenAI(
            base_url='https://api-inference.modelscope.cn/v1',
            api_key=api_key,
        )

        print("正在连接 ModelScope API...")

        # 测试文本请求（不需要图片）
        response = client.chat.completions.create(
            model='Qwen/Qwen3.5-27B',
            messages=[{
                'role': 'user',
                'content': '你好，请简短地自我介绍。'
            }],
            max_tokens=100,
        )

        result = response.choices[0].message.content
        print("✅ ModelScope 连接成功！")
        print(f"\n   响应示例:")
        print(f"   {result[:100]}...")
        return True

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n   可能的原因:")
        print("   1. API Key 不正确")
        print("   2. 网络连接问题")
        print("   3. ModelScope API 服务故障")
        return False


def test_llm_module():
    """测试 LLM 模块"""
    print("\n" + "=" * 50)
    print("🤖 测试 LLM 模块")
    print("=" * 50)

    try:
        from utils.llm import get_llm_provider, call_llm_api

        provider = get_llm_provider()
        print(f"✅ LLM 模块加载成功")
        print(f"   当前提供商: {provider}")

        if provider != 'modelscope':
            print(f"\n⚠️  警告: 当前使用的是 {provider} 提供商")
            print(f"   如需使用 ModelScope，请在 .env 中设置:")
            print(f"   LLM_PROVIDER=modelscope")

        return True

    except Exception as e:
        print(f"❌ LLM 模块加载失败: {e}")
        return False


def create_test_image():
    """创建测试图片"""
    print("\n" + "=" * 50)
    print("🖼️  创建测试图片")
    print("=" * 50)

    try:
        from PIL import Image, ImageDraw

        # 创建一个简单的测试图片
        img = Image.new('RGB', (200, 200), color='white')
        draw = ImageDraw.Draw(img)

        # 绘制一些形状
        draw.rectangle([50, 50, 150, 150], fill='blue')
        draw.ellipse([70, 70, 130, 130], fill='red')

        # 保存图片
        test_dir = 'test_images'
        os.makedirs(test_dir, exist_ok=True)
        image_path = os.path.join(test_dir, 'test_image.jpg')
        img.save(image_path)

        print(f"✅ 测试图片已创建: {image_path}")
        return image_path

    except ImportError:
        print("❌ pillow 未安装，无法创建测试图片")
        print("   运行: pip install pillow")
        return None
    except Exception as e:
        print(f"❌ 创建测试图片失败: {e}")
        return None


def test_image_analysis(image_path):
    """测试图片分析"""
    print("\n" + "=" * 50)
    print("📸 测试图片分析")
    print("=" * 50)

    if not image_path or not os.path.exists(image_path):
        print("❌ 测试图片不存在")
        return False

    try:
        from openai import OpenAI
        import os

        api_key = os.environ.get('MODELSCOPE_API_KEY')
        client = OpenAI(
            base_url='https://api-inference.modelscope.cn/v1',
            api_key=api_key,
        )

        # 使用本地文件路径
        image_url = f"file://{os.path.abspath(image_path)}"

        print(f"分析图片: {image_path}")

        response = client.chat.completions.create(
            model='Qwen/Qwen3.5-27B',
            messages=[{
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': '请描述这幅图片中包含的内容。'
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': image_url
                        }
                    }
                ]
            }],
            max_tokens=200,
        )

        result = response.choices[0].message.content
        print("✅ 图片分析成功！")
        print(f"\n   分析结果:")
        print(f"   {result}")
        return True

    except Exception as e:
        print(f"❌ 图片分析失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "=" * 48 + "╗")
    print("║" + " " * 10 + "ModelScope LLM 测试工具" + " " * 15 + "║")
    print("╚" + "=" * 48 + "╝")

    results = []

    # 运行所有测试
    results.append(("API Key 配置", test_api_key()))
    results.append(("依赖检查", test_imports()))
    results.append(("API 连接", test_connection()))
    results.append(("LLM 模块", test_llm_module()))

    # 创建和测试图片
    image_path = create_test_image()
    if image_path:
        results.append(("图片分析", test_image_analysis(image_path)))

    # 打印总结
    print("\n" + "=" * 50)
    print("📊 测试总结")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {name}")

    print(f"\n总体: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！你可以开始使用 ModelScope LLM 了。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
