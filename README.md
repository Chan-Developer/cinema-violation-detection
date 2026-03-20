# 智慧影院行为检测系统

## 这是什么

这是一个针对电影院场景的AI行为检测系统。核心想法很简单：**用计算机视觉（YOLO）检测影院里的人和物体，然后用大模型看这些检测结果并分析是否有违规行为（比如抽烟、拍照等）**。

为什么要这样搞？因为影院违规行为（吸烟、录视频等）对其他观众体验影响很大，传统的监控员巡查效率太低。这个系统可以自动检测并告警，让管理员快速处理。

**核心技术栈**：
- **后端**：Flask + SQLAlchemy + JWT认证
- **检测**：YOLOv8x（自动识别人、手机、烟雾等）
- **分析**：大语言模型（支持OpenAI、智谱、千问、ModelScope）
- **前端**：Vue 3 + Element Plus
- **数据库**：MySQL 8.0

## 工作流程

```
上传图片/视频
    ↓
YOLOv8提取人、物体位置 → 在图上画绿色检测框
    ↓
编码标注图片为base64
    ↓
发给大模型看（"图片上有绿色框，请分析有没有人在抽烟")
    ↓
大模型返回分析结果（"检测到2个人，左边的人可能在拍照，右边的人看起来在抽烟")
    ↓
前端显示标注图片 + LLM分析 + 检测结果
```

## 快速开始

### 前提条件
- Python 3.8+
- MySQL 5.7+ 或 MySQL 8.0（推荐）
- Node.js 14+（仅当需要修改前端时）

### 方式一：通过 `.venv` 启动（推荐）

#### Windows（PowerShell）
```powershell
# 1. 创建并激活虚拟环境（首次执行）
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库（确保 MySQL 已启动）
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS cinema_detection CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 4. 配置环境变量
Copy-Item .env.example .env
# 按实际情况修改 DB_HOST/DB_USER/DB_PASSWORD

# 5. 初始化并启动
python init_db.py
python app.py
```

#### Linux/macOS
```bash
# 1. 创建并激活虚拟环境（首次执行）
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库（确保 MySQL 已启动）
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS cinema_detection CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 4. 配置环境变量
cp .env.example .env
# 按实际情况修改 DB_HOST/DB_USER/DB_PASSWORD

# 5. 初始化并启动
python init_db.py
python app.py
```

启动成功后访问 **http://localhost:9500**
- 用户名：`admin`
- 密码：`admin123`

## LLM分析：这是项目的核心亮点

讲道理，YOLOv8检测对象已经不难了，难的是**理解这些检测结果代表什么**。比如：
- 检测到"phone"不一定违规（可能是工作人员）
- 检测到"person"和"smoke"一起，才是违规

所以我们集成了大语言模型来做这个"理解"的工作。核心流程是：

1. **YOLO检测**：框出图片中的人、手机、烟雾等
2. **编码图片**：把带框的图片变成base64发给LLM
3. **LLM分析**：大模型看这个带框的图，用自己的理解分析行为
4. **返回分析**：得到自然语言的分析结果

### 支持的LLM提供商

在 `.env` 里配置，选一个就行：

```bash
# ModelScope - 国内推荐（免费配额，响应快）
LLM_PROVIDER=modelscope
MODELSCOPE_API_KEY=你的key

# OpenAI - 效果最好（需要付费）
LLM_PROVIDER=openai
OPENAI_API_KEY=你的key

# 其他...
LLM_PROVIDER=zhipu      # 智谱
LLM_PROVIDER=qwen       # 通义千问
```

不配置的话会自动用本地规则分析（但效果不如LLM）。

## 项目结构简述

```
project/
├── api/                    # API端点（Flask蓝图）
│   ├── auth.py            # 登录、用户管理
│   ├── cinema.py          # 影院、影厅管理
│   ├── camera.py          # 摄像头管理
│   ├── detect.py          # 检测API（这是核心）
│   ├── alarm.py           # 报警管理
│   ├── dashboard.py       # 仪表盘数据
│   └── role.py            # 权限管理
├── models/                 # 数据库模型
├── services/
│   └── detection.py       # YOLO检测引擎
├── utils/
│   └── llm.py            # LLM分析（核心逻辑）
├── frontend/              # Vue 3前端
│   ├── src/views/        # 各个页面
│   ├── src/layouts/      # 布局
│   └── dist/             # 编译好的文件
├── config.py             # 配置
├── app.py                # 入口
└── requirements.txt      # Python依赖
```

## 主要页面和功能

| 页面 | 干什么 | 谁能用 |
|-----|---------|--------|
| **图片检测** | 上传图片/视频，看检测结果和LLM分析 | 所有人 |
| **报警管理** | 查看系统发现的违规事件 | 所有人 |
| **仪表盘** | 数据统计、系统状态 | 所有人 |
| **影院管理** | 配置影院、影厅、座位 | 管理员/经理 |
| **用户管理** | 增删改查用户账号 | 管理员 |
| **角色管理** | 配置权限 | 管理员 |

## 部署方案

### 1. 本地开发环境

就按上面"快速开始"的步骤来。前端已经编译好了，不用自己再build。

### 2. 生产环境部署（推荐：Linux服务器）

#### 方案A：Gunicorn + Nginx

```bash
# 1. 安装Gunicorn
pip install gunicorn

# 2. 启动Flask应用（后台运行）
gunicorn -w 4 -b 0.0.0.0:5000 app:app &

# 3. Nginx配置（/etc/nginx/sites-enabled/default）
upstream cinema_app {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    # 增大文件上传限制（检测API会上传视频）
    client_max_body_size 200M;

    location / {
        proxy_pass http://cinema_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# 4. 重启Nginx
sudo systemctl restart nginx
```

#### 方案B：使用Docker Compose

项目根目录有 `docker-compose.yml`，一键启动MySQL + Flask：

```bash
# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

#### 方案C：使用systemd管理服务

创建 `/etc/systemd/system/cinema-detection.service`：

```ini
[Unit]
Description=Cinema Detection System
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/home/www-data/cinema-detection
Environment="PATH=/usr/local/bin"
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
KillSignal=SIGTERM
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

然后：
```bash
sudo systemctl daemon-reload
sudo systemctl start cinema-detection
sudo systemctl enable cinema-detection  # 开机自启
```

### 3. 域名 + HTTPS（推荐）

用Let's Encrypt免费SSL证书：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

Nginx配置改成：
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # ... 其他配置
}

# 80端口重定向到443
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## 环境配置

编辑 `.env` 文件（复制 `.env.example` 改改就行）：

```bash
# Flask配置
FLASK_ENV=development
SECRET_KEY=生成一个随机字符串
JWT_SECRET_KEY=生成另一个随机字符串

# MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=cinema_detection

# LLM提供商（选一个）
LLM_PROVIDER=modelscope
MODELSCOPE_API_KEY=你的key

# YOLO模型配置
YOLO_MODEL_PATH=yolov8x.pt
YOLO_DEVICE=cpu       # 改成cuda用GPU
YOLO_CONFIDENCE=0.5   # 置信度阈值
ENABLE_YOLO=true
```

## 常见问题

### MySQL连接失败

```
Error: MySQL Connection refused
```

**原因**：MySQL没启动或密码错了

**解决**：
```bash
# 检查MySQL运行状态
sudo systemctl status mysql    # Linux
brew services list | grep mysql  # macOS

# 测试连接
mysql -u root -p -h localhost cinema_detection

# 如果还是不行，检查.env里的DB_PASSWORD是否正确
```

### 检测API返回空结果

```json
{"success": true, "detections": [], "llm_description": "..."}
```

这不是错误，说明图片里没检测到YOLOv8的目标对象。LLM会自动生成描述。

### 前端页面加载失败

```
Cannot GET /
```

**可能原因**：
1. 后端没启动
2. 前端资源没编译

**解决**：
```bash
# 确保后端启动
python3 app.py

# 重新编译前端（如有修改）
cd frontend
npm install && npm run build
cd ..
```

### 端口9500被占用

```bash
# 查看占用进程
lsof -i :9500

# 杀死它
kill -9 <PID>

# 或改端口（app.py最后一行）
socketio.run(app, host='0.0.0.0', port=8080, debug=True)
```

### LLM调用失败

```
ModelScope API 调用失败: ...
```

**原因**：API Key配置错了

**解决**：
1. 检查.env文件中MODELSCOPE_API_KEY是否正确
2. 换个LLM提供商试试（改LLM_PROVIDER）
3. 不配置LLM_PROVIDER的话系统会自动用本地规则分析

### 数据库初始化失败

```bash
# 完全重置数据库
mysql -u root -p cinema_detection < /dev/null

# 然后重启app.py
python3 app.py
```

## 生产环境建议

1. **数据库备份**：定期备份MySQL
   ```bash
   mysqldump -u root -p cinema_detection > backup.sql
   ```

2. **文件存储**：检测图片保存在`static/alarms/`，建议定期清理或用对象存储（阿里OSS等）

3. **LLM成本控制**：OpenAI会收费，建议用国内免费的ModelScope或智谱

4. **监控日志**：生产环境改成
   ```python
   FLASK_ENV=production  # 不显示详细错误
   DEBUG=False
   ```

5. **反向代理缓存**：Nginx可以缓存静态资源加快速度

## API快速参考

### 图片检测（最常用的）
```bash
POST /api/detect
Content-Type: multipart/form-data
Authorization: Bearer <token>

返回：
{
  "success": true,
  "detections": [
    {"class": "person", "confidence": 0.95, "box": [10, 20, 100, 150]},
    {"class": "phone", "confidence": 0.87, "box": [50, 60, 80, 120]}
  ],
  "annotated_image": "data:image/jpeg;base64,...",
  "llm_description": "大模型的分析结果..."
}
```

### 登录
```bash
POST /api/auth/login
{"username": "admin", "password": "admin123"}

返回：
{"access_token": "..."}
```

完整的API文档启动后访问 `http://localhost:9500/api-test.html`

## 内置角色和权限

系统有4个预设角色，不同用户有不同权限：

- **管理员**：完全权限，管理用户和系统配置
- **影院经理**：管理自己影院的设备和数据
- **监控员**：查看报警并标记处理
- **运维**：管理监控设备和系统

## 技术细节

### YOLO模型下载
第一次运行时，系统会自动下载YOLOv8x模型（~130MB）到 `~/.yolov8/`。需要科学上网或换镜像。

### 前端UI风格
用了紫粉色系（#7c3aed主色），响应式设计，PC和手机都好用。

### JWT认证
所有API都需要JWT Token。登录后得到Token，在HTTP Header里加：
```
Authorization: Bearer <your_token>
```

## 许可证

MIT License - 随便用

---

**当前版本**：1.0.0 | **最后更新**：2026-03-13

有问题或建议？欢迎反馈！
