# 🚀 启动指南

## 系统要求

| 组件 | 版本 | 备注 |
|------|------|------|
| Python | 3.8+ | 必需 |
| MySQL | 5.7+ | 必需 |
| Node.js | 14+ | 开发前端时需要 |

---

## 快速启动（推荐）

### Linux/macOS

```bash
cd project
chmod +x start.sh
./start.sh
```

### Windows

```cmd
cd project
start.bat
```

脚本会自动：
1. ✅ 检查Python环境
2. ✅ 安装依赖包
3. ✅ 检查MySQL连接
4. ✅ 创建数据库（如不存在）
5. ✅ 启动应用

---

## 手动启动

### 1. 配置数据库

确保MySQL已启动并创建数据库：

```bash
# 登录MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE IF NOT EXISTS cinema_detection
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

关键依赖：
- Flask - Web框架
- Flask-JWT-Extended - JWT认证
- SQLAlchemy - ORM
- PyMySQL - MySQL驱动
- python-dotenv - 环境变量

### 3. 启动应用

```bash
python3 app.py
```

应该看到：
```
====================================
影院不文明行为检测系统
====================================
访问地址: http://localhost:9500
默认管理员账号: admin / admin123
====================================
```

---

## 数据库初始化说明

### 自动初始化

启动 app.py 时，系统会**自动**：

1. ✅ 创建所有表结构
2. ✅ 初始化4个内置角色：
   - `admin` - 系统管理员
   - `manager` - 影院经理
   - `operator` - 监控员
   - `maintenance` - 运维

3. ✅ 初始化报警类型：
   - `photo` - 拍照违规
   - `smoke` - 吸烟违规
   - `crowd` - 人群拥挤
   - `walk` - 不文明行为

4. ✅ 初始化报警级别：
   - `critical` - 严重（红色）
   - `high` - 高（橙色）
   - `medium` - 中（黄色）
   - `low` - 低（蓝色）

5. ✅ 创建默认管理员用户：
   - 用户名: `admin`
   - 密码: `admin123`

6. ✅ 创建演示数据：
   - 1个演示影院
   - 3个演示影厅
   - 多个演示摄像头
   - 多个演示用户

### 手动重置数据库

如需完全重置：

```bash
# 1. 登录MySQL
mysql -u root -p cinema_detection

# 2. 删除所有表
DROP TABLE IF EXISTS alarm_notifications;
DROP TABLE IF EXISTS alarms;
DROP TABLE IF EXISTS alarm_levels;
DROP TABLE IF EXISTS alarm_types;
DROP TABLE IF EXISTS video_streams;
DROP TABLE IF EXISTS camera_status;
DROP TABLE IF EXISTS cameras;
DROP TABLE IF EXISTS seats;
DROP TABLE IF EXISTS halls;
DROP TABLE IF EXISTS cinemas;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;

# 3. 退出
EXIT;

# 4. 重新启动 app.py
python3 app.py
```

---

## 环境配置

### .env 文件

创建 `.env` 文件配置环境变量（复制 `.env.example`）：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root123    # 修改为您的密码
DB_NAME=cinema_detection

# LLM 配置（可选）
# 启用其中一个
# LLM_PROVIDER=modelscope
# MODELSCOPE_API_KEY=your-key
```

---

## 常见问题

### Q: MySQL 连接失败

**原因**：
- MySQL 未启动
- 数据库用户/密码错误
- 数据库不存在

**解决**：
```bash
# 1. 检查 MySQL 是否运行
mysql -u root -p

# 2. 修改 config.py 中的数据库配置
# DB_HOST, DB_USER, DB_PASSWORD

# 3. 创建数据库
CREATE DATABASE cinema_detection CHARACTER SET utf8mb4;
```

### Q: Python 依赖安装失败

**原因**：
- pip 版本过旧
- 网络连接问题

**解决**：
```bash
# 升级 pip
pip install --upgrade pip

# 重新安装
pip install -r requirements.txt -i https://pypi.org/simple/
```

### Q: 端口 9500 已被占用

**原因**：
- 应用已在运行
- 其他程序占用了该端口

**解决**：
```bash
# 查看占用进程（Linux/macOS）
lsof -i :9500

# 杀死进程
kill -9 <PID>

# 或修改 app.py 最后一行，更改端口
socketio.run(app, host='0.0.0.0', port=8080, debug=True)
```

### Q: 前端无法加载

**原因**：
- 前端资源未编译
- 路径配置错误

**解决**：
```bash
# 编译前端
cd frontend
npm install
npm run build
cd ..

# 重启后端
python3 app.py
```

### Q: 数据库初始化失败

**可能的日志输出**：
```
sqlalchemy.exc.ProgrammingError: (pymysql.err.ProgrammingError)
(1064, "You have an error in your SQL syntax...")
```

**解决**：
```bash
# 1. 删除数据库
mysql -u root -p -e "DROP DATABASE cinema_detection;"

# 2. 重启 app.py（会自动创建）
python3 app.py
```

---

## 生产环境部署

### 使用 Gunicorn + Nginx

```bash
# 1. 安装 Gunicorn
pip install gunicorn

# 2. 启动应用
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 3. Nginx 反向代理配置
# /etc/nginx/sites-available/default
upstream app {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 使用 Docker

```bash
docker build -t cinema-detection .
docker run -d -p 9500:9500 \
  -e DB_HOST=mysql \
  -e DB_USER=root \
  -e DB_PASSWORD=root123 \
  cinema-detection
```

---

## 故障排查清单

```
□ Python 已安装 (python3 --version)
□ MySQL 已启动 (mysql -u root -p)
□ 依赖已安装 (pip list | grep -E "flask|sqlalchemy")
□ 数据库存在 (mysql -e "SHOW DATABASES;")
□ .env 文件配置正确
□ 端口 9500 未被占用
□ 防火墙允许 9500 端口
```

---

## 获取帮助

启动应用后访问：
- 主应用：http://localhost:9500
- API 文档：http://localhost:9500/api/health
- 测试工具：http://localhost:9500/test.html

遇到问题请检查：
1. 后端日志输出
2. 浏览器控制台（F12）
3. MySQL 错误日志
4. 配置文件设置

