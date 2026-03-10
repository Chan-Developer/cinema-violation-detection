@echo off
REM 影院不文明行为检测系统 - Windows启动脚本

echo =====================================
echo   智慧影院 - 行为检测系统启动
echo =====================================
echo.

REM 检查 Python
echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装或不在PATH中
    pause
    exit /b 1
)
echo ✓ Python已安装
echo.

REM 检查依赖
echo [2/4] 检查依赖包...
if exist requirements.txt (
    pip install -q -r requirements.txt
    echo ✓ 依赖包已安装
) else (
    echo 错误: 未找到 requirements.txt
    pause
    exit /b 1
)
echo.

REM 检查 MySQL
echo [3/4] 检查 MySQL...
python << 'PYEOF'
import sys
try:
    import mysql.connector
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root123'
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS cinema_detection CHARACTER SET utf8mb4")
    conn.commit()
    cursor.close()
    conn.close()
    print("✓ MySQL数据库已就绪")
except Exception as e:
    print(f"❌ MySQL错误: {e}")
    print("\n故障排查:")
    print("1. 确保MySQL已启动")
    print("2. 默认用户: root, 密码: root123")
    print("3. 修改密码请编辑 config.py")
    sys.exit(1)
PYEOF

if errorlevel 1 (
    pause
    exit /b 1
)
echo.

REM 启动应用
echo [4/4] 启动应用...
echo.
echo =====================================
echo   系统启动成功!
echo =====================================
echo.
echo   访问地址:  http://localhost:9500
echo   默认账号:  admin
echo   默认密码:  admin123
echo.
echo   按 Ctrl+C 停止服务
echo.

python app.py
pause
