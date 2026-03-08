#!/usr/bin/env python3
"""
Unit tests for user CRUD operations
测试用户的增删改查操作是否正常工作
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:9500"
ADMIN_USER = {"username": "admin", "password": "admin123"}

class TestUserAPI:
    def __init__(self):
        self.token = None
        self.admin_user_id = None

    def login(self):
        """Step 1: Login and get token"""
        print("\n[1] 登录测试...")
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=ADMIN_USER,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")

        if response.status_code == 200 and result.get('success'):
            self.token = result['access_token']
            self.admin_user_id = result['user']['id']
            print(f"✅ 登录成功! Token: {self.token[:50]}...")
            return True
        else:
            print(f"❌ 登录失败!")
            return False

    def get_roles(self):
        """Get available roles"""
        print("\n[2] 获取角色列表...")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"{BASE_URL}/api/auth/roles",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")

        if response.status_code == 200 and result.get('success'):
            print(f"✅ 获取角色成功!")
            return result.get('roles', [])
        else:
            print(f"❌ 获取角色失败!")
            return []

    def create_user(self, username, password, real_name, role_id):
        """Create a new user"""
        print(f"\n[3] 创建用户: {username}...")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        data = {
            "username": username,
            "password": password,
            "real_name": real_name,
            "email": f"{username}@cinema.com",
            "phone": "13800138001",
            "role_id": role_id,
            "status": 1
        }

        response = requests.post(
            f"{BASE_URL}/api/auth/users",
            json=data,
            headers=headers
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Request: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")

        if response.status_code == 200 and result.get('success'):
            print(f"✅ 创建用户成功! 用户ID: {result['user']['id']}")
            return result['user']['id']
        else:
            print(f"❌ 创建用户失败!")
            print(f"Error: {result.get('message', 'Unknown error')}")
            return None

    def get_users(self):
        """Get users list"""
        print(f"\n[4] 获取用户列表...")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"{BASE_URL}/api/auth/users?page=1&per_page=20",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        result = response.json()

        if response.status_code == 200 and result.get('success'):
            print(f"✅ 获取用户列表成功!")
            print(f"Total users: {result['total']}")
            for user in result['users']:
                role_name = user['role'] if isinstance(user['role'], str) else user['role'].get('name', 'unknown')
                print(f"  - {user['username']} ({user['real_name']}) - {role_name}")
            return result['users']
        else:
            print(f"❌ 获取用户列表失败!")
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return []

    def update_user(self, user_id, **kwargs):
        """Update user"""
        print(f"\n[5] 更新用户 ID={user_id}...")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        response = requests.put(
            f"{BASE_URL}/api/auth/users/{user_id}",
            json=kwargs,
            headers=headers
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Request: {json.dumps(kwargs, indent=2, ensure_ascii=False)}")
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")

        if response.status_code == 200 and result.get('success'):
            print(f"✅ 更新用户成功!")
            return True
        else:
            print(f"❌ 更新用户失败!")
            return False

    def delete_user(self, user_id):
        """Delete user"""
        print(f"\n[6] 删除用户 ID={user_id}...")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        response = requests.delete(
            f"{BASE_URL}/api/auth/users/{user_id}",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")

        if response.status_code == 200 and result.get('success'):
            print(f"✅ 删除用户成功!")
            return True
        else:
            print(f"❌ 删除用户失败!")
            return False

    def run_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("用户管理 API 单元测试")
        print("=" * 60)

        # Test 1: Login
        if not self.login():
            print("\n❌ 登录失败，无法继续测试！")
            return False

        # Test 2: Get roles
        roles = self.get_roles()
        if not roles:
            print("\n❌ 获取角色失败!")
            return False

        operator_role_id = next((r['id'] for r in roles if r['name'] == 'operator'), 3)

        # Test 3: Create user
        test_user_id = self.create_user(
            username=f"test_user_{int(__import__('time').time())}",
            password="TestPass123",
            real_name="测试用户",
            role_id=operator_role_id
        )

        if test_user_id is None:
            print("\n❌ 创建用户失败，无法继续测试!")
            return False

        # Test 4: Get users
        users = self.get_users()
        if not users:
            print("\n❌ 获取用户列表失败!")
            return False

        # Test 5: Update user
        if not self.update_user(test_user_id, real_name="更新后的用户名"):
            print("\n❌ 更新用户失败!")
            return False

        # Test 6: Delete user
        if not self.delete_user(test_user_id):
            print("\n❌ 删除用户失败!")
            return False

        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)
        return True

if __name__ == '__main__':
    tester = TestUserAPI()
    success = tester.run_tests()
    sys.exit(0 if success else 1)
