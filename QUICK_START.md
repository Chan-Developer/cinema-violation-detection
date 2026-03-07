# 快速开始 (Docker + MySQL)

这个文件说明如何快速启动应用，使用Docker MySQL数据库。

## 前置要求

- **Docker** & **Docker Compose** ([安装指南](https://docs.docker.com/get-docker/))
- **Python 3.8+**

## 🚀 3分钟快速启动

### 方式 1: 使用启动脚本（推荐）

#### macOS/Linux:
```bash
chmod +x start.sh
./start.sh
```

#### Windows:
```bash
start.bat
```

脚本会自动：
1. ✅ 启动 Docker MySQL
2. ✅ 创建虚拟环境
3. ✅ 安装依赖
4. ✅ 创建 .env 配置文件

然后运行:
```bash
python app.py
```

---

### 方式 2: 使用 Makefile（Linux/macOS）

```bash
# 第一次使用 - 安装所有依赖
make install

# 启动 MySQL
make docker-up

# 启动应用
make start
```

---

### 方式 3: 手动步骤

#### 1. 启动 MySQL

```bash
docker-compose up -d
```

验证连接:
```bash
docker-compose ps  # 查看容器是否运行
```

#### 2. 安装依赖

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

#### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，使用 Docker MySQL 配置：
```ini
DB_HOST=mysql
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root123
DB_NAME=cinema_detection
```

#### 4. 启动应用

```bash
python app.py
```

---

## 📱 访问应用

| 服务 | 地址 | 账号 |
|------|------|------|
| **应用** | http://localhost:9500 | admin / admin123 |
| **数据库管理** | http://localhost:8081 | root / root123 |

---

## 📊 数据库连接测试

```bash
# 查看数据库日志
docker-compose logs mysql

# 进入 MySQL 容器
docker-compose exec mysql mysql -uroot -proot123

# 执行 SQL
docker-compose exec mysql mysql -uroot -proot123 -e "USE cinema_detection; SHOW TABLES;"
```

---

## 🛑 停止应用

```bash
# 停止应用 (Ctrl+C)

# 停止 MySQL
docker-compose stop

# 彻底清除（包括数据）
docker-compose down -v
```

---

## ⚙️ 常见问题

### Q: 如何修改 MySQL 密码？
编辑 `docker-compose.yml`，修改 `MYSQL_ROOT_PASSWORD`：
```yaml
MYSQL_ROOT_PASSWORD: your_new_password
```

### Q: 如何连接本地 MySQL（不使用Docker）？
在 `.env` 中修改：
```ini
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
```

### Q: 数据库连接错误？
```bash
# 确认 MySQL 已启动
docker-compose ps

# 查看 MySQL 日志
docker-compose logs mysql

# 重启 MySQL
docker-compose restart mysql
```

### Q: 端口被占用？
编辑 `docker-compose.yml`，修改端口映射：
```yaml
ports:
  - "3307:3306"  # 改为其他端口
```

---

## 📚 详细文档

- **Docker 配置**: [DOCKER_SETUP.md](DOCKER_SETUP.md)
- **项目文档**: [README.md](README.md)

---

## 🎯 下一步

1. ✅ 应用已启动
2. 🔐 修改默认密码（admin / admin123）
3. 🎬 配置真实的摄像头RTSP地址
4. 🤖 接入检测算法（YOLOv8/OpenVINO等）
5. 🚀 部署到生产环境

需要帮助? 查看 [DOCKER_SETUP.md](DOCKER_SETUP.md) 获取详细说明。
