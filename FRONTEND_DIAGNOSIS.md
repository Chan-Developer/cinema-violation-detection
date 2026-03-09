# 🔍 前端添加操作失败诊断指南

## 🎯 您遇到的问题
前端页面上所有的添加操作都失败了

## 📋 快速诊断步骤

### 步骤1: 打开浏览器开发者工具

**Mac**: 按 `Command + Option + I` (或 `Command + Option + J`)
**Windows**: 按 `F12` (或 `Ctrl + Shift + I`)

### 步骤2: 查看Console标签

点击顶部菜单栏的 **Console** 标签，查看是否有红色错误信息

**常见错误**：
```
❌ 跨域错误 (CORS Error)
❌ Token无效 (Token invalid)
❌ API地址错误 (API URL wrong)
❌ 网络错误 (Network error)
```

### 步骤3: 查看Network标签

1. 点击 **Network** 标签
2. 刷新页面或执行操作
3. 查看列表中的请求
4. 点击红色失败的请求
5. 查看 **Response** 标签，看返回的具体错误

**应该看到的**：
```
POST /api/auth/users 200 OK ✅
POST /api/cinemas 200 OK ✅
```

**如果失败会显示**：
```
❌ 404 Not Found
❌ 401 Unauthorized
❌ 403 Forbidden
❌ 500 Server Error
```

### 步骤4: 查看响应内容

在Network标签中，右键点击失败的请求，选择 **Copy as cURL**，告诉我：
- 请求URL
- 响应状态码
- 响应Body中的错误信息

---

## 🔧 常见问题自检清单

### ✅ 检查1: 后端API是否运行

在浏览器访问：
```
http://localhost:9500/api/health
```

**应该看到**：
```json
{
  "status": "ok",
  "time": "2026-03-09T...",
  "version": "1.0.0"
}
```

**如果看到错误**：
- ❌ 无法连接 → 后端没有启动
  解决：运行 `python3 app.py`

### ✅ 检查2: 是否成功登录

在Console中运行：
```javascript
localStorage.getItem('token')
```

**应该看到**：
- ✅ 一长串token字符串
- ❌ null → 没有登录，先登录

### ✅ 检查3: 前端API基础URL

在Console中运行：
```javascript
import.meta.env.VITE_API_BASE
```

**应该看到**：
- ✅ `http://localhost:9500/api`
- ❌ `undefined` 或 `null` → 环境变量未设置
- ❌ 其他地址 → API地址配置错误

### ✅ 检查4: Token是否有效

在Console中运行：
```javascript
// 查看token内容
const token = localStorage.getItem('token');
const parts = token.split('.');
const payload = JSON.parse(atob(parts[1]));
console.log(payload);
```

应该看到：
```javascript
{
  fresh: false,
  iat: 1773024... // 生成时间
  exp: 1773111... // 过期时间
  sub: "1" // 用户ID
  ...
}
```

---

## 📱 完整问题排查流程

### 问题类型1: 登录页面

```
场景: 输入admin/admin123后点击登录
错误信息: "操作失败" 或 "登录失败"

排查步骤:
1. 打开Network标签
2. 点击登录按钮
3. 找到 /api/auth/login 请求
4. 查看Status（应该是200）
5. 查看Response，看错误内容

常见原因:
❌ 后端没启动 → 状态502 Bad Gateway
❌ 密码错误 → 返回 "用户名或密码错误"
❌ 跨域问题 → CORS错误在Console
```

### 问题类型2: 添加用户

```
场景: 在用户管理页面点击"添加用户"按钮
错误信息: 对话框中显示"操作失败"

排查步骤:
1. 确认已登录 (localStorage.getItem('token'))
2. 打开Network标签
3. 填写表单 (用户名、密码、姓名、角色)
4. 点击"保存"按钮
5. 找到 /api/auth/users 请求

可能的错误信息:
❌ "缺少必要参数" → 没填用户名或role_id
❌ "用户名已存在" → 用户名重复
❌ "权限不足" → Token中role不是admin
```

### 问题类型3: 添加影院

```
场景: 在影院管理页面点击"添加影院"
错误信息: 对话框显示"操作失败"

排查步骤:
1. 打开Network标签
2. 点击"添加影院"
3. 填写: 影院名称、地址、城市
4. 点击"保存"
5. 查看 /api/cinemas 请求的Response

常见错误:
❌ "影院名称不能为空" → 没填名称
❌ "权限不足" → 角色不是admin或manager
```

---

## 🐛 具体的错误解决方案

### 错误: "操作失败" (无具体信息)

**原因分析**：前端捕获了异常但没有具体错误消息

**查看方法**：
```javascript
// 在Console中运行看详细错误
await fetch('/api/auth/users', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
  body: JSON.stringify({
    username: 'test',
    password: 'pass',
    real_name: '测试',
    role_id: 3
  })
})
.then(r => r.json())
.then(d => console.log(JSON.stringify(d, null, 2)))
.catch(e => console.error(e))
```

### 错误: CORS错误

**现象**：
```
Access to XMLHttpRequest at 'http://localhost:9500/api/auth/users'
from origin 'http://localhost:5173' has been blocked by CORS policy
```

**原因**：前端和后端端口不同
**解决**：
- 确保后端运行在 `http://localhost:9500`
- 确保前端配置的API_BASE是 `http://localhost:9500/api`

### 错误: 401 Unauthorized

**现象**：请求返回401状态

**原因**：Token无效或过期
**解决**：
1. 清除localStorage
2. 重新登录

```javascript
// 在Console中清除
localStorage.clear()
location.reload()
```

---

## 📝 请提供的具体信息

当您遇到添加失败时，请告诉我：

1️⃣ **具体现象**：
   - 哪个添加操作失败（用户/影院/摄像头/影厅/角色）？
   - 显示的错误信息是什么？

2️⃣ **浏览器Console中的错误**：
   - 有红色错误信息吗？
   - 什么内容？

3️⃣ **Network标签中的信息**：
   - 请求状态码是多少？
   - 响应Body中是什么？

4️⃣ **您填的表单数据**：
   - 填了哪些字段？
   - 具体值是什么？

---

## 🚀 快速恢复方案

如果所有操作都失败，请按顺序尝试：

### 方案1: 重启后端
```bash
# 停止后端
killall python3

# 重启后端
python3 app.py
```

### 方案2: 清除前端缓存
```javascript
// 在浏览器Console中运行
localStorage.clear()
sessionStorage.clear()
location.reload()
```

### 方案3: 完整重置
```bash
# 1. 停止后端
killall python3

# 2. 在浏览器中清除所有数据
# DevTools → Application → Storage → Clear Site Data

# 3. 重启后端
python3 app.py

# 4. 重新登录
```

---

## ✅ 验证一切正常

当一切恢复正常后，您应该能看到：

1. ✅ 登录成功，进入仪表盘
2. ✅ 点击"添加用户"，对话框打开
3. ✅ 填写表单，点击保存
4. ✅ 看到"添加成功"提示
5. ✅ 用户列表中出现新用户

---

## 📞 下一步

请按照上面的诊断步骤操作，然后告诉我：
- 具体看到什么错误
- Network标签中的状态码
- 响应内容

这样我就能准确诊断并修复问题！
