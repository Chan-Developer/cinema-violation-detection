#!/usr/bin/env python3
"""
数据库初始化脚本
Database Initialization Script
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db

def init_database():
    """初始化数据库"""
    app, socketio = create_app('development')
    
    with app.app_context():
        print("🔄 正在初始化数据库...")
        
        # 创建所有表
        db.create_all()
        print("✅ 表结构已创建")
        
        # 导入模型以触发初始化
        from models import Role, AlarmType, AlarmLevel, User
        
        # 初始化角色
        Role.init_roles()
        print("✅ 角色已初始化 (admin, manager, operator, maintenance)")
        
        # 初始化报警类型
        AlarmType.init_types()
        print("✅ 报警类型已初始化 (photo, smoke, crowd, walk)")
        
        # 初始化报警级别
        AlarmLevel.init_levels()
        print("✅ 报警级别已初始化 (critical, high, medium, low)")
        
        # 创建默认管理员
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role:
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    real_name='系统管理员',
                    email='admin@cinema.com',
                    phone='13800138000',
                    role_id=admin_role.id,
                    status=1
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ 默认管理员已创建 (admin/admin123)")
            else:
                print("⚠️  管理员已存在")
        
        print("\n" + "="*40)
        print("✨ 数据库初始化完成!")
        print("="*40)
        print("\n访问信息:")
        print("  地址: http://localhost:9500")
        print("  账号: admin")
        print("  密码: admin123")
        print("\n启动服务:")
        print("  python3 app.py")

if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        print("\n请检查:")
        print("  1. MySQL 是否已启动")
        print("  2. 数据库配置是否正确 (config.py)")
        print("  3. 数据库是否存在 (cinema_detection)")
        sys.exit(1)
