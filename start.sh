#!/bin/bash

# 影院不文明行为检测系统 - 启动脚本

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  智慧影院 - 行为检测系统启动${NC}"
echo -e "${GREEN}=====================================${NC}"

# 检查 Python
echo -e "${YELLOW}[1/4] 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python已安装${NC}"

# 检查依赖
echo -e "${YELLOW}[2/4] 检查依赖包...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ 依赖包已安装${NC}"
else
    echo -e "${RED}❌ 未找到 requirements.txt${NC}"
    exit 1
fi

# 检查 MySQL
echo -e "${YELLOW}[3/4] 检查 MySQL...${NC}"
python3 << 'PYEOF'
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

if [ $? -ne 0 ]; then
    exit 1
fi

# 启动应用
echo -e "${YELLOW}[4/4] 启动应用...${NC}"
echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  系统启动成功!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo -e "  🌐 访问地址:  http://localhost:9500"
echo -e "  👤 默认账号:  admin"
echo -e "  🔐 默认密码:  admin123"
echo ""
echo -e "${YELLOW}  按 Ctrl+C 停止服务${NC}"
echo ""

python3 app.py
