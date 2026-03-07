# Docker MySQL 使用指南

## 概述

本项目已配置为使用 MySQL 数据库，并提供了 Docker Compose 配置文件用于快速启动 MySQL 服务。

## 系统要求

- Docker & Docker Compose
- Python 3.8+
- pip

## 快速开始

### 1. 启动 MySQL (使用 Docker)

```bash
# 进入项目目录
cd /Users/mr.chen/Documents/Project/毕设/毕设1/project

# 启动MySQL和PhpMyAdmin服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

**预期输出：**
```
CONTAINER ID   IMAGE              COMMAND                  CREATED             STATUS
xxxxx          mysql:8.0          "docker-entrypoint.s…"   10 seconds ago      Up 8 seconds
xxxxx          phpmyadmin:latest  "/docker-entrypoint.…"   10 seconds ago      Up 3 seconds
```

### 2. 验证 MySQL 连接

```bash
# 方式1：使用 docker-compose 执行 MySQL 命令
docker-compose exec mysql mysql -uroot -proot123 -e "SELECT VERSION();"

# 方式2：使用 PhpMyAdmin Web 界面
# 打开浏览器访问: http://localhost:8081
# 用户名: root
# 密码: root123
```

### 3. 配置应用环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件 (如果使用Docker MySQL，使用以下配置):
# DB_HOST=mysql
# DB_PORT=3306
# DB_USER=root
# DB_PASSWORD=root123
# DB_NAME=cinema_detection
```

### 4. 安装 Python 依赖

```bash
# 创建虚拟环境 (推荐)
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 5. 启动应用

```bash
python app.py
```

**预期输出：**
```
==================================================
影院不文明行为检测系统
==================================================
访问地址: http://localhost:9500
默认管理员账号: admin / admin123
==================================================
```

访问 http://localhost:9500 使用默认账号登录。

---

## 数据库配置详解

### Docker 环境变量

`docker-compose.yml` 中的 MySQL 配置：

| 环境变量 | 值 | 说明 |
|---------|-----|------|
| `MYSQL_ROOT_PASSWORD` | `root123` | Root 用户密码 |
| `MYSQL_DATABASE` | `cinema_detection` | 初始化的数据库名 |
| `MYSQL_USER` | `cinema_user` | 应用用户名（可选） |
| `MYSQL_PASSWORD` | `cinema_pass123` | 应用用户密码（可选） |

### 应用连接字符串

当使用 Docker MySQL 时，在 `.env` 中配置：

```ini
DB_HOST=mysql          # Docker 容器名称（Docker网络内可直接使用）
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root123
DB_NAME=cinema_detection
```

当使用本地 MySQL 时：

```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root123
DB_NAME=cinema_detection
```

---

## 常用命令

### Docker Compose 命令

```bash
# 启动服务（后台运行）
docker-compose up -d

# 查看日志
docker-compose logs -f mysql

# 停止服务
docker-compose stop

# 停止并移除容器
docker-compose down

# 移除容器并清空数据
docker-compose down -v

# 进入 MySQL 容器
docker-compose exec mysql bash
```

### MySQL 操作

```bash
# 通过 Docker 执行 MySQL 命令
docker-compose exec mysql mysql -uroot -proot123 cinema_detection

# 导出数据库
docker-compose exec mysql mysqldump -uroot -proot123 cinema_detection > backup.sql

# 导入数据库
docker-compose exec -T mysql mysql -uroot -proot123 cinema_detection < backup.sql
```

---

## 故障排除

### 问题 1: 无法连接到 MySQL

**症状：** `pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")`

**解决方案：**
1. 确认 Docker 已启动：`docker-compose ps`
2. 检查 MySQL 容器日志：`docker-compose logs mysql`
3. 确认环境变量配置正确（`.env` 文件）
4. 如果容器未运行，重启：`docker-compose up -d`

### 问题 2: 端口被占用

**症状：** `Error response from daemon: Ports are not available`

**解决方案：**
1. 找到占用 3306 端口的进程并关闭
2. 或修改 `docker-compose.yml` 中的端口映射，例如：`"3307:3306"`

### 问题 3: 数据库编码错误

**症状：** 中文显示乱码

**解决方案：**
- Docker Compose 已配置 `utf8mb4` 字符集
- 确保 SQLAlchemy 连接字符串包含：`?charset=utf8mb4`
- 应用中已自动配置，无需手动修改

### 问题 4: 数据持久化问题

**症状：** 重启容器后数据丢失

**解决方案：**
- Docker Compose 已配置 `mysql_data` 命名卷
- 数据自动持久化到 `/var/lib/mysql`
- 除非执行 `docker-compose down -v`，否则数据不会丢失

---

## 扩展配置

### 修改 MySQL 版本

编辑 `docker-compose.yml` 中的 `mysql` 服务：

```yaml
mysql:
  image: mysql:8.0  # 改为其他版本，如 5.7, 8.1 等
```

### 禁用 PhpMyAdmin

删除或注释 `docker-compose.yml` 中的 `phpmyadmin` 服务。

### 使用自定义 MySQL 配置

创建 `my.cnf` 文件并挂载到容器：

```yaml
volumes:
  - ./my.cnf:/etc/mysql/conf.d/my.cnf
```

---

## 本地 MySQL 使用（不使用 Docker）

如果你已安装本地 MySQL，可以跳过 Docker 步骤：

1. 创建数据库：
   ```sql
   CREATE DATABASE cinema_detection CHARACTER SET utf8mb4;
   ```

2. 配置 `.env` 文件指向本地 MySQL：
   ```ini
   DB_HOST=localhost
   ```

3. 启动应用：
   ```bash
   python app.py
   ```

---

## 备份和恢复

### 定期备份

```bash
# 自动备份脚本 (backup.sh)
docker-compose exec -T mysql mysqldump -uroot -proot123 cinema_detection > backups/cinema_$(date +%Y%m%d_%H%M%S).sql
```

### 恢复数据

```bash
docker-compose exec -T mysql mysql -uroot -proot123 cinema_detection < backups/cinema_20240101_120000.sql
```

---

## 下一步

- 配置真实的视频流和检测算法
- 部署到生产环境（使用 Kubernetes 或云服务）
- 设置数据库复制和主从架构

需要帮助? 参考本项目的完整文档。
