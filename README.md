# 🎬 智慧影院 - 行为检测系统

基于YOLOv8和大型语言模型的电影院不文明行为智能检测系统

## ✨ 核心功能

- **实时检测**: YOLOv8x视频监控与实时分析
- **智能分析**: 集成LLM进行场景描述和异常判断
- **报警管理**: 等级化报警系统（严重/警告/信息）
- **可视化**: 个性化UI设计，检测结果展示
- **权限管理**: 基于角色的访问控制（4个内置角色）
- **监控设备**: 支持RTSP流和视频文件上传

## 🚀 快速启动

### Linux/macOS（推荐）
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

### 手动启动
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 创建数据库（MySQL需要先启动）
python3 init_db.py

# 3. 启动应用
python3 app.py
```

启动成功后访问: **http://localhost:9500**
- 账号: `admin`
- 密码: `admin123`

> 详细启动说明请查看 [STARTUP_GUIDE.md](STARTUP_GUIDE.md)

## 📊 系统架构

```
project/
├── api/                 # Flask蓝图
│   ├── auth.py         # 认证与用户管理
│   ├── cinema.py       # 影院与影厅管理
│   ├── camera.py       # 摄像头管理
│   ├── detect.py       # 检测API (YOLO + LLM)
│   ├── alarm.py        # 报警管理
│   ├── dashboard.py    # 仪表板
│   └── role.py         # 角色管理
├── models/             # 数据库模型
├── services/           # 业务逻辑
│   └── detection.py    # YOLO检测引擎
├── utils/              # 工具函数
│   └── llm.py         # LLM分析
├── frontend/           # Vue 3 + Element Plus
│   ├── src/
│   │   ├── views/     # 检测、报警、管理页面
│   │   ├── layouts/   # 个性化布局
│   │   └── router/    # 路由配置
│   └── dist/          # 编译输出
└── app.py             # Flask应用入口
```

## 🎯 核心API端点

### 检测接口
- `POST /api/detect` - 上传图片/视频进行YOLOv8检测 + LLM分析

### 认证
- `POST /api/auth/login` - 登录
- `GET /api/auth/users` - 用户列表
- `POST /api/auth/users` - 新增用户

### 管理
- `GET /api/roles` - 获取角色
- `GET /api/cinemas` - 影院列表
- `GET /api/cameras` - 摄像头列表
- `GET /api/alarms` - 报警列表

## 💻 主要页面

| 页面 | 功能 | 访问权限 |
|-----|------|--------|
| 仪表盘 | 统计数据、实时监控 | 全部 |
| 图片检测 | YOLO检测 + LLM分析 | 全部 |
| 报警管理 | 报警列表、处理报警 | 全部 |
| 影院管理 | 影院/影厅配置 | 管理员/经理 |
| 用户管理 | 用户增删改查 | 管理员 |
| 角色管理 | 权限配置 | 管理员 |

## 🎨 UI特色

- **个性化配色**: 紫粉色系渐变设计
  - 主色: #7c3aed (紫色)
  - 辅色: #d084d0 (粉色)
  - 浅色: #a78bdb (淡紫)
- **流畅动画**: 页面过渡、卡片悬停
- **响应式设计**: 完美支持PC和移动端
- **Element Plus**: 成熟的Vue 3组件库

## 🔐 内置角色

| 角色 | 权限描述 |
|-----|--------|
| 管理员 | 完全权限，管理系统和用户 |
| 影院经理 | 管理本影院数据和设备 |
| 监控员 | 查看报警并处理异常 |
| 运维 | 设备管理和系统维护 |

## 🛠️ LLM集成

支持多种LLM提供商进行图片分析：

```bash
# ModelScope (默认，推荐)
export LLM_PROVIDER=modelscope
export MODELSCOPE_API_KEY=your-key

# OpenAI
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your-key

# 或其他提供商...
```

检测流程:
1. 用户上传图片/视频
2. YOLOv8提取特征并识别对象
3. LLM根据检测结果生成智能描述
4. 返回标注图片+检测结果+LLM分析

## 📝 配置文件

编辑 `config.py` 修改数据库和存储:

```python
SQLALCHEMY_DATABASE_URI = 'mysql://user:pass@localhost/cinema'
UPLOAD_FOLDER = 'uploads'
ALLOWED_IMAGE = {'jpg', 'jpeg', 'png', 'gif'}
ALLOWED_VIDEO = {'mp4', 'avi', 'mov', 'webm'}
```

## ✅ 测试工具

内置API测试页面:
- http://localhost:9500/test.html - 完整测试工具
- http://localhost:9500/api-test.html - 简化版

可直接在页面中进行:
- 登录测试
- 数据CRUD测试
- 检测API测试

## 🚨 常见问题

**Q: 后端无法启动?**
A: 检查MySQL是否运行，确保config.py数据库URL正确

**Q: 前端加载失败?**
A: 清除浏览器缓存并刷新页面，检查后端是否启动

**Q: 检测返回空结果?**
A: 当图片中没有可检测对象时正常返回空，LLM会自动生成描述

**Q: 功能无权限访问?**
A: 用admin账号登录并检查用户角色权限

## 📚 技术栈

**后端**
- Flask: Web框架
- Flask-JWT-Extended: JWT认证
- SQLAlchemy: ORM
- OpenAI SDK: LLM接口

**前端**
- Vue 3: 框架
- TypeScript: 类型支持
- Element Plus: UI组件
- Pinia: 状态管理

**AI/ML**
- YOLOv8x: 对象检测
- OpenAI/GLM-4V/Qwen: 图像理解
- ModelScope: 大模型推理

**基础设施**
- MySQL 8.0: 数据库
- Docker Compose: 容器编排
- Nginx: 反向代理

## 📄 LICENSE

MIT License

---

**版本**: 1.0.0 | **更新**: 2026-03-10
