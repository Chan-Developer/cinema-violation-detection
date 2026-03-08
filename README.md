# 🎬 影院不文明行为检测系统

## 🚀 快速启动

### 1. 启动数据库
```bash
docker-compose up -d
```

### 2. 启动后端
```bash
python3 app.py
```

### 3. 访问应用
- 地址: http://localhost:9500
- 账号: admin
- 密码: admin123

## ✨ 最新修复（第二期）

**问题修复**:
1. ✅ **角色管理** - 新增完整的角色管理功能（CRUD）
2. ✅ **API字段修复** - 检测API返回字段改为 `class`（前端兼容）
3. ✅ **图片检测** - 完全支持上传图片并返回检测结果 + LLM描述

**添加的文件**:
- `api/role.py` - 角色管理API
- `frontend/src/views/RoleManage.vue` - 角色管理前端
- `test_complete.py` - 完整功能测试脚本

## ✅ 功能状态

| 功能 | 状态 | API | 测试 |
|------|------|-----|------|
| 用户管理 | ✅ | POST /api/auth/users | ✅ |
| 角色管理 | ✅ | POST /api/roles | ✅ |
| 影院管理 | ✅ | POST /api/cinemas | ✅ |
| 摄像头管理 | ✅ | POST /api/cameras | ✅ |
| 图片检测 | ✅ | POST /api/detect | ✅ |
| 报警管理 | ✅ | GET /api/alarms | ✅ |
| 仪表盘 | ✅ | GET /api/dashboard | ✅ |

## 🧪 完整测试命令

```bash
# 运行完整功能测试
python3 test_complete.py
```

结果示例：
```
✅ 1. 用户登录
✅ 2. 角色管理: 获取4个角色
✅ 3. 用户创建: 用户创建成功
✅ 4. 影院创建: 影院创建成功
✅ 5. 摄像头创建: 摄像头创建成功
✅ 6. 图片检测: 图片检测成功
✅ 7. 报警列表: 获取报警
✅ 8. 仪表盘: 仪表盘数据成功

总计: 8/8 成功
```

## 📋 核心改动

### api/role.py (新文件)
- 完整的角色CRUD操作
- 权限检查（仅admin可修改）
- 关联检查（删除前检查是否有用户使用）

### api/detect.py (修复)
- 改进检测结果格式化
- 统一返回 `class` 字段（与前端兼容）
- LLM描述自动降级方案

### frontend/src/views/RoleManage.vue (新文件)
- 角色管理UI组件
- 新增、编辑、删除角色
- 内置角色保护

### MainLayout.vue (更新)
- 添加角色管理菜单项
- 仅admin用户可见

## 🎯 前端菜单结构

| 菜单 | 角色权限 | 路径 |
|------|--------|------|
| 仪表盘 | 全部 | / |
| 实时监控 | 全部 | /monitor |
| 图片检测 | 全部 | /detection |
| 报警管理 | 全部 | /alarms |
| 影院管理 | admin, manager | /cinemas |
| 设备管理 | 全部 | /cameras |
| 用户管理 | admin | /users |
| 角色管理 | admin | /roles |
| 系统设置 | 全部 | /settings |

## 📊 API端点总览

### 角色管理
```
GET    /api/roles              - 获取所有角色
GET    /api/roles/<id>         - 获取角色详情
POST   /api/roles              - 创建角色
PUT    /api/roles/<id>         - 更新角色
DELETE /api/roles/<id>         - 删除角色
```

### 用户管理
```
GET    /api/auth/users         - 获取用户列表
POST   /api/auth/users         - 创建用户
PUT    /api/auth/users/<id>    - 更新用户
DELETE /api/auth/users/<id>    - 删除用户
```

### 图片检测
```
POST   /api/detect             - 上传图片/视频检测
GET    /api/detect/status/<id> - 获取检测状态
```

### 影院管理
```
GET    /api/cinemas            - 获取影院列表
POST   /api/cinemas            - 创建影院
PUT    /api/cinemas/<id>       - 更新影院
DELETE /api/cinemas/<id>       - 删除影院
```

### 摄像头管理
```
GET    /api/cameras            - 获取摄像头列表
POST   /api/cameras            - 创建摄像头
PUT    /api/cameras/<id>       - 更新摄像头
DELETE /api/cameras/<id>       - 删除摄像头
```

## 📞 常见问题

**前端操作失败？**
- 检查浏览器控制台的Network标签，看API返回什么
- 确保已登录并有有效的JWT Token
- 检查用户角色权限

**图片检测返回空结果？**
- 这是正常现象，当图片中没有可检测的物体时返回空
- LLM描述会显示"图片中没有检测到任何物体"

**角色无法删除？**
- 系统内置角色（admin, manager, operator, maintenance）无法删除
- 如果有用户使用该角色，需要先修改用户的角色再删除

## 🔒 安全说明

- 所有API都要求JWT认证
- 用户操作有角色权限检查
- 密码存储使用bcrypt加密
- 支持刷新Token续期

## 📦 项目结构

```
project/
├── api/                    # 后端API
│   ├── auth.py            # 认证与用户管理
│   ├── role.py            # 角色管理（新增）
│   ├── cinema.py          # 影院管理
│   ├── camera.py          # 摄像头管理
│   ├── alarm.py           # 报警管理
│   ├── detect.py          # 图片检测
│   └── ...
├── frontend/              # 前端
│   ├── src/
│   │   ├── views/
│   │   │   ├── RoleManage.vue   # 角色管理（新增）
│   │   │   ├── UserManage.vue
│   │   │   ├── CinemaManage.vue
│   │   │   ├── Detection.vue
│   │   │   └── ...
│   │   ├── router/
│   │   └── stores/
│   └── dist/              # 编译后前端
├── models/                # 数据库模型
├── services/              # 业务逻辑
├── utils/                 # 工具函数
├── test_complete.py       # 完整功能测试（新增）
└── app.py                 # Flask应用入口
```

## ✅ 最后验证

已验证所有8个核心功能：
- ✅ 用户登录
- ✅ 角色管理
- ✅ 用户CRUD
- ✅ 影院CRUD
- ✅ 摄像头CRUD
- ✅ 图片检测 + LLM描述
- ✅ 报警管理
- ✅ 仪表盘统计

