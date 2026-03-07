from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
import eventlet

socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')

# 连接的用户
connected_users = {}

def init_socketio(app):
    """初始化SocketIO"""
    socketio.init_app(app, message_queue=None, async_mode='eventlet')
    return socketio


# ============== 事件处理 ==============

@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    print(f"客户端连接: {request.sid}")
    connected_users[request.sid] = {
        'sid': request.sid,
        'user_id': None,
        'username': None,
        'role': None,
        'cinema_id': None
    }
    emit('connected', {'sid': request.sid, 'message': '连接成功'})


@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开"""
    print(f"客户端断开: {request.sid}")
    if request.sid in connected_users:
        del connected_users[request.sid]


@socketio.on('authenticate')
def handle_authenticate(data):
    """用户认证"""
    user_id = data.get('user_id')
    username = data.get('username')
    role = data.get('role')
    cinema_id = data.get('cinema_id')
    
    if request.sid in connected_users:
        connected_users[request.sid].update({
            'user_id': user_id,
            'username': username,
            'role': role,
            'cinema_id': cinema_id
        })
        
        # 根据角色加入不同的房间
        if role == 'admin':
            join_room('admin')
        elif role == 'manager':
            join_room(f'cinema_{cinema_id}')
        elif role == 'operator':
            join_room('operators')
        elif role == 'maintenance':
            join_room('maintenance')
        
        emit('authenticated', {'success': True, 'message': '认证成功'})


@socketio.on('join_room')
def handle_join_room(data):
    """加入房间"""
    room = data.get('room')
    if room:
        join_room(room)
        emit('joined', {'room': room})


@socketio.on('leave_room')
def handle_leave_room(data):
    """离开房间"""
    room = data.get('room')
    if room:
        leave_room(room)
        emit('left', {'room': room})


@socketio.on('ping')
def handle_ping():
    """心跳检测"""
    emit('pong', {'time': eventlet.time.time()})


# ============== 报警推送 ==============

def emit_alarm(alarm_data, target_roles=None, target_cinema_id=None):
    """推送报警到客户端"""
    # 广播所有报警
    socketio.emit('new_alarm', alarm_data)
    
    # 按角色推送
    if target_roles:
        for role in target_roles:
            if role == 'admin':
                socketio.emit('new_alarm', alarm_data, room='admin')
            elif role == 'manager' and target_cinema_id:
                socketio.emit('new_alarm', alarm_data, room=f'cinema_{target_cinema_id}')
            elif role == 'operator':
                socketio.emit('new_alarm', alarm_data, room='operators')


def emit_stream_status(camera_id, status):
    """推送视频流状态"""
    socketio.emit('stream_status', {
        'camera_id': camera_id,
        'status': status,
        'time': eventlet.time.time()
    })


def emit_detection_result(camera_id, result):
    """推送检测结果"""
    socketio.emit('detection_result', {
        'camera_id': camera_id,
        'result': result,
        'time': eventlet.time.time()
    })


def emit_statistics(data):
    """推送统计信息"""
    socketio.emit('statistics', data)
