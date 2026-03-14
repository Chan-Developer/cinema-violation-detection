import eventlet
eventlet.monkey_patch()

import os
import sys
from dotenv import load_dotenv

# Load .env before importing config so env values are applied.
load_dotenv(override=True)

import datetime
from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
from models import db, Role, User, Cinema, AlarmType, AlarmLevel

# 加载 .env 环境变量（覆盖已存在的环境变量，避免旧值残留）

# 初始化扩展
jwt = JWTManager()

def create_app(config_name='development'):
    """应用工厂"""
    app = Flask(__name__, 
               template_folder='frontend/dist',
               static_folder='frontend/dist/assets',
               static_url_path='/assets')
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 初始化SocketIO
    from services.websocket import init_socketio
    socketio = init_socketio(app)
    
    # 注册蓝图
    from api import register_blueprints
    register_blueprints(app)
    
    # 注册路由
    register_routes(app)
    
    # 创建数据库表
    with app.app_context():
        init_database()
    
    return app, socketio


def register_routes(app):
    """注册基础路由"""
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/api/health')
    def health():
        return jsonify({
            'status': 'ok',
            'time': datetime.datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
    @app.route('/api/init', methods=['POST'])
    def init_data():
        """初始化演示数据"""
        try:
            init_database()
            return jsonify({'success': True, 'message': '数据初始化成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    @app.route('/<path:path>')
    def serve_spa(path):
        """SPA路由回退 — 先检查静态文件，再返回index.html"""
        if path.startswith('api/') or path.startswith('socket.io/'):
            return jsonify({'error': 'Not Found'}), 404

        # 检查是否是存在的静态文件（.html等）
        static_file = os.path.join('frontend/dist', path)
        if os.path.isfile(static_file):
            return send_from_directory('frontend/dist', path)

        return render_template('index.html')


def init_database():
    """初始化数据库"""
    db.create_all()
    
    # 初始化角色
    Role.init_roles()
    
    # 初始化报警类型
    AlarmType.init_types()
    
    # 初始化报警级别
    AlarmLevel.init_levels()
    
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
    
    # 创建演示影院
    if Cinema.query.count() == 0:
        cinema = Cinema(
            name='示例影院',
            address='北京市朝阳区示例路100号',
            city='北京',
            district='朝阳区',
            phone='010-12345678',
            contact='张经理',
            status=1
        )
        db.session.add(cinema)
        db.session.commit()
        
        # 创建影厅
        halls = [
            {'name': '1号厅', 'hall_type': 'IMAX', 'rows': 10, 'cols': 20},
            {'name': '2号厅', 'hall_type': '普通', 'rows': 8, 'cols': 15},
            {'name': '3号厅', 'hall_type': 'VIP', 'rows': 6, 'cols': 12},
        ]
        # 创建影厅
        from models import Hall, Seat
        rows_list = 'ABCDEFGHIJKLMNOP'
        for h_data in halls:
            hall = Hall(
                cinema_id=cinema.id,
                name=h_data['name'],
                hall_type=h_data['hall_type'],
                rows=h_data['rows'],
                cols=h_data['cols'],
                total_seats=h_data['rows'] * h_data['cols'],
                status=1
            )
            db.session.add(hall)
            db.session.flush()
            
            # 创建座位
            for r in range(h_data['rows']):
                row_name = rows_list[r]
                for n in range(1, h_data['cols'] + 1):
                    seat = Seat(
                        hall_id=hall.id,
                        row=row_name,
                        number=n,
                        seat_type='normal',
                        status=1
                    )
                    db.session.add(seat)
        
        # 创建演示摄像头
        from models import Camera
        cameras = [
            {'name': '1号厅-入口', 'hall_index': 0, 'position': '入口', 'rtsp': 'rtsp://demo:demo@fake.com/stream1'},
            {'name': '1号厅-座位区', 'hall_index': 0, 'position': '座位区', 'rtsp': 'rtsp://demo:demo@fake.com/stream2'},
            {'name': '2号厅-中央', 'hall_index': 1, 'position': '中央', 'rtsp': 'rtsp://demo:demo@fake.com/stream3'},
            {'name': '3号厅-入口', 'hall_index': 2, 'position': '入口', 'rtsp': 'rtsp://demo:demo@fake.com/stream4'},
        ]
        
        all_halls = Hall.query.all()
        for c_data in cameras:
            hall = all_halls[c_data['hall_index']] if c_data['hall_index'] < len(all_halls) else all_halls[0]
            camera = Camera(
                name=c_data['name'],
                cinema_id=cinema.id,
                hall_id=hall.id,
                rtsp_url=c_data['rtsp'],
                position=c_data['position'],
                detection_enabled=1,
                detection_types='photo,smoke,crowd,walk',
                manufacturer='Hikvision',
                model='DS-2CD2043G2',
                status=0
            )
            db.session.add(camera)
        
        # 创建演示用户
        manager_role = Role.query.filter_by(name='manager').first()
        operator_role = Role.query.filter_by(name='operator').first()
        maintenance_role = Role.query.filter_by(name='maintenance').first()
        
        users = [
            {'username': 'manager1', 'real_name': '李经理', 'role': manager_role, 'cinema': cinema},
            {'username': 'operator1', 'real_name': '王监控', 'role': operator_role},
            {'username': 'tech1', 'real_name': '张运维', 'role': maintenance_role},
        ]
        
        for u_data in users:
            if not User.query.filter_by(username=u_data['username']).first():
                user = User(
                    username=u_data['username'],
                    real_name=u_data['real_name'],
                    email=f"{u_data['username']}@cinema.com",
                    role_id=u_data['role'].id,
                    cinema_id=u_data.get('cinema').id if u_data.get('cinema') else None,
                    status=1
                )
                user.set_password('123456')
                db.session.add(user)
        
        db.session.commit()
    
    print("数据库初始化完成!")


# ============== 启动应用 ==============

if __name__ == '__main__':

    
    app, socketio = create_app('development')
    
    print("=" * 50)
    print("影院不文明行为检测系统")
    print("=" * 50)
    print("访问地址: http://localhost:9500")
    print("默认管理员账号: admin / admin123")
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=9500, debug=True)
