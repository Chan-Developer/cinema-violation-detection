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

## ✨ 已修复问题

**问题**: 添加用户、影院、上传图片都失败
**原因**: JWT Token处理逻辑不正确
**方案**: 修改JWT identity为字符串，使用additional_claims传递额外信息
**修改文件**:
- `api/auth.py` - 修复JWT生成和权限检查
- `api/cinema.py` - 修复权限检查逻辑

## ✅ 功能状态

| 功能 | 状态 | API |
|------|------|-----|
| 用户管理 | ✅ | POST /api/auth/users |
| 影院管理 | ✅ | POST /api/cinemas |
| 图片检测 | ✅ | POST /api/detect |

## 🧪 测试命令

```bash
# 登录
TOKEN=$(curl -s -X POST http://localhost:9500/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# 添加用户
curl -X POST http://localhost:9500/api/auth/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"pass","real_name":"测试","role_id":3}'

# 添加影院
curl -X POST http://localhost:9500/api/cinemas \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"影院名称","address":"地址","city":"城市"}'

# 上传图片检测
curl -X POST http://localhost:9500/api/detect \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@image.jpg"
```

## 📋 代码修改详解

### auth.py 修改

1. **修改import** - 添加get_jwt
```python
from flask_jwt_extended import get_jwt, get_jwt_identity
```

2. **修改login函数** - JWT Token包含额外信息
```python
additional_claims = {
    'role': user.role.name,
    'role_id': user.role_id,
    'cinema_id': user.cinema_id
}
create_access_token(identity=str(user.id), additional_claims=additional_claims)
```

3. **添加帮助函数** - 统一获取用户信息
```python
def get_current_user_with_claims():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    return user_id, claims
```

4. **修改所有路由** - 使用new helper函数
- 所有权限检查改为: `_, claims = get_current_user_with_claims()`
- 改为: `if claims.get('role') != 'admin':`

### cinema.py 修改

1. **修改import** - 添加get_jwt
2. **添加helper函数** - 同auth.py
3. **修改所有路由** - 统一处理JWT

## 🎯 核心改动

| 文件 | 改动 | 影响 |
|------|------|------|
| auth.py | JWT额外信息 | 修复所有auth相关API |
| cinema.py | 权限检查 | 影院CRUD正常 |
| detect.py | 无需修改 | 检测API正常 |

## ✅ 测试验证

所有操作已通过测试：
- ✅ 创建用户（数据写入MySQL）
- ✅ 创建影院（数据写入MySQL）
- ✅ 上传图片检测（YOLO + LLM）
- ✅ 更新用户/影院
- ✅ 删除用户/影院

## 📞 问题排查

**JWT认证失败**
- 确保使用最新的Token
- 检查 Authorization header 格式: `Bearer <token>`
- 重启Flask应用使代码生效

**数据库操作失败**
- 检查MySQL是否运行: `docker-compose ps`
- 检查.env配置

**检测失败**
- 检查文件格式 (JPG/PNG/GIF/MP4)
- 检查文件大小 (< 200MB)
