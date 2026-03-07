#!/bin/bash

# 影院不文明行为检测系统 - 启动脚本
# 使用方法: ./start.sh

set -e

echo "=================================="
echo "影院不文明行为检测系统 - 启动脚本"
echo "=================================="
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未检测到 Docker"
    echo "请先安装 Docker: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: 未检测到 Docker Compose"
    echo "请先安装 Docker Compose"
    exit 1
fi

echo "✓ Docker 已安装"
echo ""

# 第一步: 启动 MySQL
echo "📦 第一步: 启动 MySQL 容器..."
if docker-compose up -d; then
    echo "✓ MySQL 启动成功"
    echo ""

    # 等待 MySQL 启动
    echo "⏳ 等待 MySQL 就绪..."
    sleep 5

    # 检查 MySQL 连接
    if docker-compose exec -T mysql mysql -uroot -proot123 -e "SELECT 1;" > /dev/null 2>&1; then
        echo "✓ MySQL 连接成功"
    else
        echo "⚠️  MySQL 正在启动，请稍候..."
        sleep 5
    fi
else
    echo "❌ MySQL 启动失败"
    exit 1
fi

echo ""
echo "📋 第二步: 检查 Python 环境..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate || . venv/Scripts/activate

echo "✓ 虚拟环境已激活"
echo ""

# 第三步: 安装依赖
echo "📚 第三步: 安装 Python 依赖..."
pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt
echo "✓ 依赖安装完成"
echo ""

# 第四步: 配置环境变量
echo "⚙️  第四步: 配置环境变量..."
if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    cp .env.example .env
    echo "✓ .env 文件已创建"
    echo "  提示: 如果使用Docker MySQL，请在.env中设置:"
    echo "    DB_HOST=mysql"
    echo "    DB_PORT=3306"
    echo "    DB_USER=root"
    echo "    DB_PASSWORD=root123"
else
    echo "✓ .env 文件已存在"
fi

echo ""
echo "=================================="
echo "✓ 启动完成！"
echo "=================================="
echo ""
echo "🌐 访问地址:"
echo "   应用: http://localhost:9500"
echo "   MySQL管理: http://localhost:8081 (用户: root, 密码: root123)"
echo ""
echo "👤 默认账号:"
echo "   用户名: admin"
echo "   密码: admin123"
echo ""
echo "📖 查看日志:"
echo "   MySQL: docker-compose logs -f mysql"
echo "   应用: python app.py"
echo ""
echo "🛑 停止服务:"
echo "   docker-compose stop"
echo ""
echo "📚 详细说明请参考: DOCKER_SETUP.md"
echo ""
