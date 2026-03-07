# 📝 MySQL 迁移总结

## ✅ 完成的改动

### 1. **数据库配置**
- ✅ `config.py` - 改为使用 MySQL 连接字符串
  - 从 SQLite 改为 MySQL (PyMySQL)
  - 支持环境变量配置
  - 自动设置 UTF-8mb4 字符集

### 2. **依赖更新**
- ✅ `requirements.txt` - 添加 PyMySQL 驱动
  ```
  PyMySQL>=1.1.0
  ```

### 3. **应用配置**
- ✅ `app.py` - 添加 .env 文件加载
  ```python
  from dotenv import load_dotenv
  load_dotenv()
  ```

- ✅ `.env.example` - 更新为 MySQL 配置示例
  ```ini
  DB_HOST=localhost
  DB_PORT=3306
  DB_USER=root
  DB_PASSWORD=root123
  DB_NAME=cinema_detection
  ```

### 4. **Docker 支持**
- ✅ `docker-compose.yml` - MySQL & PhpMyAdmin 容器配置
  - MySQL 8.0
  - PhpMyAdmin Web 管理工具
  - 自动数据持久化
  - 健康检查

- ✅ `init.sql` - 数据库初始化脚本
  - 设置 UTF-8mb4 字符集
  - 创建基础索引

### 5. **启动脚本**
- ✅ `start.sh` - Linux/macOS 一键启动脚本
  - 检查 Docker 环境
  - 启动 MySQL
  - 创建虚拟环境
  - 安装依赖
  - 生成 .env 文件

- ✅ `start.bat` - Windows 一键启动脚本
  - 同上功能，适配 Windows

### 6. **Makefile**
- ✅ `Makefile` - 便捷命令集合
  ```bash
  make install      # 安装依赖
  make docker-up    # 启动 MySQL
  make docker-down  # 停止 MySQL
  make start        # 启动应用
  make db-backup    # 备份数据库
  make db-restore   # 恢复数据库
  ```

### 7. **文档**
- ✅ `QUICK_START.md` - 快速开始指南
- ✅ `DOCKER_SETUP.md` - 详细 Docker 使用文档

---

## 🚀 当前状态

### Docker 服务状态 ✓
```
✅ MySQL 8.0        (健康状态)  - 0.0.0.0:3306
✅ PhpMyAdmin      (运行中)    - 0.0.0.0:8081
✅ cinema_detection 数据库已创建
```

### 环境变量配置 ✓
```
DB_HOST=mysql          (Docker 环境)
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root123
DB_NAME=cinema_detection
```

---

## 📖 使用方法

### 方案 1: 快速启动（推荐）

#### macOS/Linux:
```bash
chmod +x start.sh
./start.sh
```

#### Windows:
```bash
start.bat
```

### 方案 2: 手动启动

```bash
# 1. 启动 MySQL
docker-compose up -d

# 2. 安装依赖
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 启动应用
python app.py
```

### 方案 3: 使用 Makefile (Linux/macOS)

```bash
make install    # 首次使用
make docker-up  # 启动 MySQL
make start      # 启动应用
```

---

## 🌐 访问地址

| 服务 | 地址 | 账号 |
|------|------|------|
| 应用 | http://localhost:9500 | admin / admin123 |
| 数据库管理 | http://localhost:8081 | root / root123 |

---

## 📊 数据库迁移说明

### 从 SQLite 到 MySQL

| 功能 | SQLite | MySQL | 状态 |
|------|--------|-------|------|
| 数据库连接 | 本地文件 | TCP/IP | ✅ |
| 字符集编码 | 单一 | UTF-8mb4 | ✅ |
| 数据持久化 | 磁盘文件 | Docker 卷 | ✅ |
| Web 管理工具 | 无 | PhpMyAdmin | ✅ |
| 性能 | 低并发 | 高并发 | ✅ |
| 数据备份 | 手动 | 自动化脚本 | ✅ |

### 应用代码兼容性

- ✅ SQLAlchemy ORM 完全兼容
- ✅ 无需修改模型代码
- ✅ 无需修改查询代码
- ✅ 自动处理数据类型转换

---

## 🔧 常用命令

### Docker 操作
```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f mysql

# 进入 MySQL 容器
docker-compose exec mysql bash

# 重启服务
docker-compose restart mysql

# 停止服务
docker-compose stop

# 完全移除
docker-compose down -v
```

### 数据库操作
```bash
# 执行 SQL
docker-compose exec mysql mysql -uroot -proot123 -e "SQL语句"

# 备份数据库
docker-compose exec -T mysql mysqldump -uroot -proot123 cinema_detection > backup.sql

# 恢复数据库
docker-compose exec -T mysql mysql -uroot -proot123 cinema_detection < backup.sql
```

### 应用操作
```bash
# 启动应用
python app.py

# 查看健康状态
curl http://localhost:9500/api/health

# 初始化演示数据
curl -X POST http://localhost:9500/api/init
```

---

## ⚠️ 注意事项

1. **首次启动**
   - MySQL 初始化需要 10-30 秒
   - 第一次访问时应用会自动初始化数据库表
   - 默认会创建演示数据

2. **数据持久化**
   - 数据存储在 Docker 命名卷 `mysql_data` 中
   - 执行 `docker-compose down` 不会删除数据
   - 执行 `docker-compose down -v` 会删除数据

3. **端口冲突**
   - MySQL: 3306 (可在 docker-compose.yml 中修改)
   - PhpMyAdmin: 8081 (可在 docker-compose.yml 中修改)
   - 应用: 9500 (在 app.py 中修改)

4. **环境变量优先级**
   - 系统环境变量 > .env 文件 > config.py 默认值

5. **性能优化**
   - 使用本地 MySQL 比 Docker 快
   - 生产环境建议使用专业数据库服务

---

## 📚 进阶配置

### 使用本地 MySQL

编辑 `.env` 文件：
```ini
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
```

### 修改 MySQL 密码

编辑 `docker-compose.yml`:
```yaml
MYSQL_ROOT_PASSWORD: new_password
```

### 使用不同 MySQL 版本

编辑 `docker-compose.yml`:
```yaml
image: mysql:5.7  # 或其他版本
```

### 增加数据库用户

```bash
docker-compose exec mysql mysql -uroot -proot123 -e \
  "CREATE USER 'app_user'@'%' IDENTIFIED BY 'app_password';" && \
docker-compose exec mysql mysql -uroot -proot123 -e \
  "GRANT ALL PRIVILEGES ON cinema_detection.* TO 'app_user'@'%'; FLUSH PRIVILEGES;"
```

---

## 🐛 故障排除

### 连接错误

```bash
# 检查 MySQL 是否运行
docker-compose ps

# 查看 MySQL 日志
docker-compose logs mysql

# 重启 MySQL
docker-compose restart mysql
```

### 端口被占用

```bash
# 查找占用 3306 的进程
lsof -i :3306  # macOS/Linux
netstat -ano | findstr :3306  # Windows

# 或修改 docker-compose.yml 中的端口
```

### 数据库编码错误

```bash
# 检查字符集
docker-compose exec mysql mysql -uroot -proot123 -e \
  "USE cinema_detection; SHOW CREATE DATABASE cinema_detection;"
```

---

## 📞 获取帮助

1. 查看详细文档: `DOCKER_SETUP.md`
2. 查看快速开始: `QUICK_START.md`
3. 查看应用文档: `README.md`
4. 检查 Docker 日志: `docker-compose logs`

---

## 🎉 下一步

1. ✅ 启动应用并确认数据库连接正常
2. 📝 修改默认管理员密码
3. 🎬 配置真实的摄像头 RTSP 地址
4. 🤖 接入检测算法（YOLOv8/OpenVINO）
5. 🚀 部署到生产环境

**享受开发！** 🚀
