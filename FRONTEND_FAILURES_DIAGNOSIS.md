# 🚨 所有添加操作失败的可能原因清单

## 🔴 致命问题（会导致所有操作失败）

### 问题1️⃣: 后端完全未运行
**症状**：
- 浏览器显示无法连接
- Network中全是红色请求
- Console中有 `Failed to fetch` 错误

**检查命令**：
```bash
curl http://localhost:9500/api/health
```

**修复**：
```bash
python3 app.py
```

---

### 问题2️⃣: Token失效或丢失
**症状**：
- 登录成功但操作时提示权限不足
- 或者直接被重定向到登录页
- Console显示 401 Unauthorized

**检查**：
```javascript
// 在Console中运行
localStorage.getItem('token')
```

**应该返回**：
```
eyJhbGciOiJIUzI1NiIsInR5...（一长串）
```

**如果返回null**：
- 没有成功登录
- 或浏览器清除了localStorage

**修复**：重新登录

---

### 问题3️⃣: 跨域（CORS）问题
**症状**：
```
Access to XMLHttpRequest ... blocked by CORS policy
```

**原因**：
- 前端访问的API地址错误
- 后端没有启用CORS

**检查**：
```javascript
// 在Console查看
console.log(import.meta.env.VITE_API_BASE)
```

**应该看到**：
```
http://localhost:9500/api
```

---

### 问题4️⃣: 权限不足
**症状**：
- 所有操作都返回 "权限不足"
- HTTP状态码 403

**原因**：
- 当前用户角色不是admin
- Token中的role信息不对

**检查**：
```javascript
// 在Console查看Token中的role
const token = localStorage.getItem('token');
const payload = JSON.parse(atob(token.split('.')[1]));
console.log(payload.role);  // 应该显示 'admin'
```

**修复**：
- 用admin账号登录
- 或者用具有该权限的账号

---

## 🟠 常见问题（会导致特定操作失败）

### 问题5️⃣: 表单数据不完整
**症状**：
```
操作失败
缺少必要参数
```

**原因**：没填必填字段

**每个表单的必填字段**：

**用户管理**：
- ✅ 用户名（username）
- ✅ 密码（password）
- ✅ 角色（role_id）
- ⚠️ 真实姓名（real_name）- 可选

**影院管理**：
- ✅ 影院名称（name）
- ⚠️ 地址（address）- 可选
- ⚠️ 城市（city）- 可选

**摄像头管理**：
- ✅ 摄像头名称（name）
- ✅ 影院（cinema_id）
- ⚠️ 影厅（hall_id）- 可选
- ⚠️ RTSP地址（rtsp_url）- 可选

**影厅管理**：
- ✅ 影厅名称（name）
- ✅ 行数（rows）- 1-26
- ✅ 列数（cols）- 1-100

**角色管理**：
- ✅ 角色名（name）
- ⚠️ 描述（description）- 可选

---

### 问题6️⃣: 数据重复
**症状**：
```
用户名已存在
角色已存在
```

**修复**：
- 使用不同的名称
- 或先删除重复的数据

---

### 问题7️⃣: 数据关联缺失
**症状**：
```
影院不存在
影厅不存在
```

**原因**：
- 选择的影院/影厅ID不存在
- 或被删除了

**修复**：
- 先创建所需的影院/影厅
- 再创建关联的数据

---

## 📊 快速诊断表

| 现象 | 可能原因 | 检查方式 |
|------|--------|---------|
| 无法打开页面 | 后端未运行 | `curl http://localhost:9500` |
| 页面打开但无法登录 | 后端错误 | 查看 /api/auth/login 响应 |
| 登录成功但操作失败 | Token无效或权限不足 | 检查 localStorage.getItem('token') |
| Network中404错误 | API地址错误 | 检查 VITE_API_BASE 配置 |
| Network中403错误 | 权限不足 | 检查Token中的role字段 |
| 显示"操作失败" | 多种原因 | 查看Network中的具体错误 |

---

## 🔧 完整恢复步骤

如果**所有操作都失败**，按以下顺序执行：

### 步骤1: 检查后端状态
```bash
# 查看后端进程
ps aux | grep app.py

# 检查API是否可用
curl http://localhost:9500/api/health
```

**预期输出**：
```json
{"status":"ok","time":"...","version":"1.0.0"}
```

**如果失败**：
```bash
# 启动后端
python3 app.py
```

### 步骤2: 清除前端缓存
```javascript
// 在浏览器Console中运行
localStorage.clear()
sessionStorage.clear()
location.reload()
```

### 步骤3: 重新登录
- 输入 admin / admin123
- 点击登录

### 步骤4: 测试添加操作
1. 进入用户管理
2. 点击添加用户
3. 填写: 用户名、密码、姓名、角色
4. 点击保存

**应该看到**：
- ✅ "添加成功" 提示
- ✅ 新用户出现在列表中

---

## 📈 成功的标志

所有操作恢复正常的标志：

```
✅ 登录页面能正常登录
✅ Network中所有API请求状态都是200
✅ 点击添加按钮能打开对话框
✅ 填写表单能点击保存
✅ 保存后显示"操作成功"提示
✅ 列表中出现新的数据
✅ Console中没有红色错误
```

---

## 💡 关键提示

1. **重启最强大**：
   ```bash
   killall python3
   python3 app.py
   ```

2. **清缓存最全面**：
   ```javascript
   localStorage.clear()
   sessionStorage.clear()
   ```

3. **重新登录最有效**：
   - 清除缓存后必须重新登录
   - 不能使用旧的token

4. **检查最细致**：
   - 打开Network标签
   - 执行操作
   - 点击失败的请求
   - 查看Response的具体内容

---

## 🆘 如果还是失败

请告诉我：

1. **您看到的具体错误信息**（截图或文字）
2. **Network标签中的Status Code**（200/404/403/500等）
3. **Response中的完整JSON**
4. **您填的具体表单数据**
5. **后端启动时是否有错误日志**

这样我就能准确诊断！
