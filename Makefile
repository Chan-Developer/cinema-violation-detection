.PHONY: help docker-up docker-down docker-logs db-backup db-restore clean install start

help:
	@echo "=================================="
	@echo "影院不文明行为检测系统 - Makefile"
	@echo "=================================="
	@echo ""
	@echo "可用命令:"
	@echo "  make install       - 安装依赖和创建虚拟环境"
	@echo "  make docker-up     - 启动 Docker MySQL 服务"
	@echo "  make docker-down   - 停止 Docker MySQL 服务"
	@echo "  make docker-logs   - 查看 Docker MySQL 日志"
	@echo "  make start         - 启动应用 (前提: MySQL已启动)"
	@echo "  make db-backup     - 备份数据库"
	@echo "  make db-restore    - 恢复数据库"
	@echo "  make clean         - 清理临时文件和日志"
	@echo ""

install:
	@echo "安装依赖..."
	@python -m venv venv
	@. venv/bin/activate && pip install -r requirements.txt
	@cp .env.example .env
	@echo "✓ 安装完成"
	@echo "  下一步: make docker-up"

docker-up:
	@echo "启动 Docker MySQL..."
	@docker-compose up -d
	@echo "✓ MySQL 已启动"
	@echo "  应用: http://localhost:9500"
	@echo "  PhpMyAdmin: http://localhost:8081"
	@echo "  下一步: make start"

docker-down:
	@echo "停止 Docker MySQL..."
	@docker-compose stop
	@echo "✓ MySQL 已停止"

docker-logs:
	@docker-compose logs -f mysql

start:
	@. venv/bin/activate && python app.py

db-backup:
	@echo "备份数据库..."
	@mkdir -p backups
	@docker-compose exec -T mysql mysqldump -uroot -proot123 cinema_detection > backups/cinema_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✓ 备份完成"

db-restore:
	@echo "恢复数据库..."
	@ls -t backups/*.sql | head -1 | xargs -I {} docker-compose exec -T mysql mysql -uroot -proot123 cinema_detection < {}
	@echo "✓ 恢复完成"

clean:
	@echo "清理临时文件..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@rm -rf .pytest_cache .coverage htmlcov
	@echo "✓ 清理完成"

# 数据库健康检查
db-health:
	@docker-compose exec -T mysql mysql -uroot -proot123 -e "SELECT 1;" && echo "✓ 数据库连接正常" || echo "❌ 数据库连接失败"
