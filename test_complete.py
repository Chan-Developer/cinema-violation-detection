#!/usr/bin/env python3
"""
完整功能测试脚本
测试所有API端点的CRUD操作
"""
import requests
import json
import sys
from pathlib import Path

API_URL = "http://localhost:9500/api"
TEST_IMAGE = "/tmp/test_image.jpg"

# 创建测试图片
from PIL import Image
img = Image.new('RGB', (100, 100), color='green')
img.save(TEST_IMAGE)

class TestRunner:
    def __init__(self):
        self.token = None
        self.results = []

    def log(self, test_name, success, message=""):
        status = "✅" if success else "❌"
        self.results.append((test_name, success, message))
        print(f"{status} {test_name}: {message}")

    def run_test(self, test_name, fn):
        try:
            result = fn()
            self.log(test_name, result[0], result[1])
        except Exception as e:
            self.log(test_name, False, str(e))

    def login(self):
        """测试登录"""
        try:
            resp = requests.post(f"{API_URL}/auth/login", json={
                "username": "admin",
                "password": "admin123"
            })
            if resp.status_code == 200:
                data = resp.json()
                if data['success']:
                    self.token = data['access_token']
                    return True, "登录成功"
            return False, f"登录失败: {resp.text}"
        except Exception as e:
            return False, str(e)

    def test_roles(self):
        """测试角色管理"""
        try:
            resp = requests.get(f"{API_URL}/roles",
                headers={"Authorization": f"Bearer {self.token}"})
            if resp.status_code == 200:
                data = resp.json()
                if data['success'] and len(data['roles']) >= 4:
                    return True, f"获取{len(data['roles'])}个角色"
            return False, "获取角色失败"
        except Exception as e:
            return False, str(e)

    def test_user_create(self):
        """测试创建用户"""
        try:
            resp = requests.post(f"{API_URL}/auth/users",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "username": f"testuser_{int(__import__('time').time())}",
                    "password": "test123",
                    "real_name": "测试用户",
                    "role_id": 3
                })
            if resp.status_code == 200:
                data = resp.json()
                if data['success']:
                    return True, "用户创建成功"
            return False, f"用户创建失败: {resp.text}"
        except Exception as e:
            return False, str(e)

    def test_cinema_create(self):
        """测试创建影院"""
        try:
            resp = requests.post(f"{API_URL}/cinemas",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "name": f"影院_{int(__import__('time').time())}",
                    "address": "测试地址",
                    "city": "北京"
                })
            if resp.status_code == 200:
                data = resp.json()
                if data['success']:
                    return True, "影院创建成功"
            return False, f"影院创建失败: {resp.text}"
        except Exception as e:
            return False, str(e)

    def test_camera_create(self):
        """测试创建摄像头"""
        try:
            # 先获取一个影院ID
            resp = requests.get(f"{API_URL}/cinemas",
                headers={"Authorization": f"Bearer {self.token}"})
            if resp.status_code != 200:
                return False, "获取影院列表失败"

            cinemas = resp.json().get('cinemas', [])
            if not cinemas:
                return False, "没有可用的影院"

            cinema_id = cinemas[0]['id']

            resp = requests.post(f"{API_URL}/cameras",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "name": "测试摄像头",
                    "cinema_id": cinema_id,
                    "rtsp_url": "rtsp://test.com/stream"
                })
            if resp.status_code == 200:
                data = resp.json()
                if data['success']:
                    return True, "摄像头创建成功"
            return False, f"摄像头创建失败: {resp.text}"
        except Exception as e:
            return False, str(e)

    def test_detection(self):
        """测试图片检测"""
        try:
            with open(TEST_IMAGE, 'rb') as f:
                files = {'file': f}
                resp = requests.post(f"{API_URL}/detect",
                    headers={"Authorization": f"Bearer {self.token}"},
                    files=files)
            if resp.status_code == 200:
                data = resp.json()
                if data['success'] and 'annotated_image' in data and 'llm_description' in data:
                    return True, "图片检测成功"
            return False, f"图片检测失败: {resp.text}"
        except Exception as e:
            return False, str(e)

    def test_alarms(self):
        """测试获取报警列表"""
        try:
            resp = requests.get(f"{API_URL}/alarms",
                headers={"Authorization": f"Bearer {self.token}"})
            if resp.status_code == 200:
                data = resp.json()
                if data['success']:
                    return True, f"获取{data['total']}条报警"
            return False, "获取报警失败"
        except Exception as e:
            return False, str(e)

    def test_dashboard(self):
        """测试仪表盘"""
        try:
            resp = requests.get(f"{API_URL}/dashboard/overview",
                headers={"Authorization": f"Bearer {self.token}"})
            if resp.status_code == 200:
                data = resp.json()
                if data['success']:
                    return True, "仪表盘数据获取成功"
            return False, "仪表盘数据获取失败"
        except Exception as e:
            return False, str(e)

    def run_all(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("开始全功能测试")
        print("="*60 + "\n")

        self.run_test("1. 用户登录", lambda: (self.login(), "")[0:2])

        if not self.token:
            print("\n❌ 登录失败，无法继续测试")
            return False

        self.run_test("2. 角色管理", self.test_roles)
        self.run_test("3. 用户创建", self.test_user_create)
        self.run_test("4. 影院创建", self.test_cinema_create)
        self.run_test("5. 摄像头创建", self.test_camera_create)
        self.run_test("6. 图片检测", self.test_detection)
        self.run_test("7. 报警列表", self.test_alarms)
        self.run_test("8. 仪表盘", self.test_dashboard)

        print("\n" + "="*60)
        print("测试总结")
        print("="*60)

        success_count = sum(1 for _, success, _ in self.results if success)
        total_count = len(self.results)

        for test_name, success, message in self.results:
            status = "✅" if success else "❌"
            print(f"{status} {test_name}: {message}")

        print(f"\n总计: {success_count}/{total_count} 成功")
        return success_count == total_count

if __name__ == '__main__':
    runner = TestRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)
