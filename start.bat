@echo off
REM 影院不文明行为检测系统 - 启动脚本 (Windows)
REM 使用方法: start.bat

chcp 65001 >nul
cls

echo ==================================
echo 影院不文明行为检测系统 - 启动脚本
echo ==================================
echo.

REM 检查Docker是否安装
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未检测到 Docker
    echo 请先安装 Docker: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

where docker-compose >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未检测到 Docker Compose
    echo 请先安装 Docker Compose
    pause
    exit /b 1
)

echo ✓ Docker 已安装
echo.

REM 第一步: 启动 MySQL
echo 📦 第一步: 启动 MySQL 容器...
docker-compose up -d
if %errorlevel% equ 0 (
    echo ✓ MySQL 启动成功
    echo.

    echo ⏳ 等待 MySQL 就绪...
    timeout /t 5 /nobreak
) else (
    echo ❌ MySQL 启动失败
    pause
    exit /b 1
)

echo.
echo 📋 第二步: 检查 Python 环境...

REM 检查虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

echo ✓ 虚拟环境已激活
echo.

REM 第三步: 安装依赖
echo 📚 第三步: 安装 Python 依赖...
pip install -q -r requirements.txt
if %errorlevel% equ 0 (
    echo ✓ 依赖安装完成
) else (
    echo ⚠️  依赖安装时出现问题，继续运行...
)
echo.

REM 第四步: 配置环境变量
echo ⚙️  第四步: 配置环境变量...
if not exist ".env" (
    echo 创建 .env 文件...
    copy .env.example .env
    echo ✓ .env 文件已创建
    echo   提示: 如果使用Docker MySQL，请在.env中设置:
    echo     DB_HOST=mysql
    echo     DB_PORT=3306
    echo     DB_USER=root
    echo     DB_PASSWORD=root123
) else (
    echo ✓ .env 文件已存在
)

echo.
echo ==================================
echo ✓ 启动完成！
echo ==================================
echo.
echo 🌐 访问地址:
echo    应用: http://localhost:9500
echo    MySQL管理: http://localhost:8081 (用户: root, 密码: root123)
echo.
echo 👤 默认账号:
echo    用户名: admin
echo    密码: admin123
echo.
echo 📖 下一步操作:
echo    1. 编辑 .env 文件，确保数据库配置正确
echo    2. 运行: python app.py
echo    3. 打开浏览器访问: http://localhost:9500
echo.
echo 📚 详细说明请参考: DOCKER_SETUP.md
echo.
pause
