from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, Camera, Cinema, CameraStatus
from utils.roles import (
    ROLE_ADMIN,
    ROLE_MAINTENANCE,
    ROLE_MANAGER,
    has_any_role,
    is_admin,
    is_manager,
    manager_cinema_id,
)

camera_bp = Blueprint('camera', __name__)


def get_current_user_info():
    """获取当前用户信息"""
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    return user_id, claims


@camera_bp.route('', methods=['GET'])
@jwt_required()
def get_cameras():
    """获取摄像头列表"""
    _, claims = get_current_user_info()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    cinema_id = request.args.get('cinema_id', type=int)
    hall_id = request.args.get('hall_id', type=int)
    status = request.args.get('status', type=int)
    keyword = request.args.get('keyword')

    query = Camera.query

    # 根据角色过滤
    scoped_cinema_id = manager_cinema_id(claims)
    if scoped_cinema_id:
        query = query.filter(Camera.cinema_id == scoped_cinema_id)
    elif cinema_id:
        query = query.filter(Camera.cinema_id == cinema_id)

    if hall_id:
        query = query.filter(Camera.hall_id == hall_id)
    if status is not None:
        query = query.filter(Camera.status == status)
    if keyword:
        query = query.filter(Camera.name.contains(keyword))

    pagination = query.order_by(Camera.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'success': True,
        'cameras': [c.to_dict(include_status=True) for c in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page
    })


@camera_bp.route('/<int:camera_id>', methods=['GET'])
@jwt_required()
def get_camera(camera_id):
    """获取摄像头详情"""
    _, claims = get_current_user_info()
    camera = Camera.query.get(camera_id)
    if not camera:
        return jsonify({'success': False, 'message': '摄像头不存在'}), 404
    if is_manager(claims) and manager_cinema_id(claims) != camera.cinema_id:
        return jsonify({'success': False, 'message': '仅可访问所属影院摄像头'}), 403
    
    return jsonify({'success': True, 'camera': camera.to_dict(include_status=True)})


@camera_bp.route('', methods=['POST'])
@jwt_required()
def create_camera():
    """创建摄像头"""
    _, claims = get_current_user_info()
    if not has_any_role(claims, ROLE_ADMIN, ROLE_MANAGER, ROLE_MAINTENANCE):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    data = request.get_json(silent=True) or {}
    name = data.get('name')
    cinema_id = data.get('cinema_id')
    if is_manager(claims):
        cinema_id = manager_cinema_id(claims)

    if not name or not cinema_id:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400

    # 验证影院存在
    cinema = Cinema.query.get(cinema_id)
    if not cinema:
        return jsonify({'success': False, 'message': '影院不存在'}), 404
    
    camera = Camera(
        name=name,
        cinema_id=cinema_id,
        hall_id=data.get('hall_id'),
        rtsp_url=data.get('rtsp_url'),
        username=data.get('username'),
        password=data.get('password'),
        position=data.get('position'),
        angle=data.get('angle'),
        mount_height=data.get('mount_height'),
        detection_enabled=data.get('detection_enabled', 1),
        detection_types=data.get('detection_types', 'photo,smoke'),
        manufacturer=data.get('manufacturer'),
        model=data.get('model'),
        ip_address=data.get('ip_address'),
        port=data.get('port'),
        status=0
    )
    
    db.session.add(camera)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '摄像头创建成功', 'camera': camera.to_dict()})


@camera_bp.route('/<int:camera_id>', methods=['PUT'])
@jwt_required()
def update_camera(camera_id):
    """更新摄像头"""
    _, claims = get_current_user_info()
    if not has_any_role(claims, ROLE_ADMIN, ROLE_MANAGER, ROLE_MAINTENANCE):
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    camera = Camera.query.get(camera_id)
    if not camera:
        return jsonify({'success': False, 'message': '摄像头不存在'}), 404
    if is_manager(claims) and manager_cinema_id(claims) != camera.cinema_id:
        return jsonify({'success': False, 'message': '仅可更新所属影院摄像头'}), 403
    
    data = request.get_json(silent=True) or {}
    
    if 'name' in data:
        camera.name = data['name']
    if 'cinema_id' in data and not is_manager(claims):
        camera.cinema_id = data['cinema_id']
    if 'hall_id' in data:
        camera.hall_id = data['hall_id']
    if 'rtsp_url' in data:
        camera.rtsp_url = data['rtsp_url']
    if 'username' in data:
        camera.username = data['username']
    if 'password' in data:
        camera.password = data['password']
    if 'position' in data:
        camera.position = data['position']
    if 'angle' in data:
        camera.angle = data['angle']
    if 'mount_height' in data:
        camera.mount_height = data['mount_height']
    if 'detection_enabled' in data:
        camera.detection_enabled = data['detection_enabled']
    if 'detection_types' in data:
        camera.detection_types = data['detection_types']
    if 'manufacturer' in data:
        camera.manufacturer = data['manufacturer']
    if 'model' in data:
        camera.model = data['model']
    if 'ip_address' in data:
        camera.ip_address = data['ip_address']
    if 'port' in data:
        camera.port = data['port']
    if 'status' in data:
        camera.status = data['status']
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': '摄像头更新成功', 'camera': camera.to_dict()})


@camera_bp.route('/<int:camera_id>', methods=['DELETE'])
@jwt_required()
def delete_camera(camera_id):
    """删除摄像头"""
    _, claims = get_current_user_info()
    if not is_admin(claims):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    camera = Camera.query.get(camera_id)
    if not camera:
        return jsonify({'success': False, 'message': '摄像头不存在'}), 404

    # 检查是否有报警关联
    from models import Alarm
    alarm_count = camera.alarms.count() if hasattr(camera, 'alarms') and camera.alarms else 0
    if alarm_count > 0:
        return jsonify({'success': False, 'message': f'该摄像头下有{alarm_count}条报警，无法删除'}), 400

    db.session.delete(camera)
    db.session.commit()

    return jsonify({'success': True, 'message': '摄像头删除成功'})


@camera_bp.route('/<int:camera_id>/status', methods=['GET'])
@jwt_required()
def get_camera_status(camera_id):
    """获取摄像头状态"""
    _, claims = get_current_user_info()
    camera = Camera.query.get(camera_id)
    if not camera:
        return jsonify({'success': False, 'message': '摄像头不存在'}), 404
    if is_manager(claims) and manager_cinema_id(claims) != camera.cinema_id:
        return jsonify({'success': False, 'message': '仅可访问所属影院摄像头'}), 403
    
    # 获取最近的status记录
    latest = CameraStatus.query.filter_by(camera_id=camera_id).order_by(
        CameraStatus.record_time.desc()
    ).first()
    
    # 统计
    total_alarms = camera.alarms.count() if camera.alarms else 0
    pending_alarms = camera.alarms.filter_by(status=0).count()
    
    return jsonify({
        'success': True,
        'camera': camera.to_dict(),
        'latest_status': latest.to_dict() if latest else None,
        'statistics': {
            'total_alarms': total_alarms,
            'pending_alarms': pending_alarms
        }
    })


@camera_bp.route('/<int:camera_id>/status', methods=['POST'])
@jwt_required()
def update_camera_status(camera_id):
    """更新摄像头状态"""
    _, claims = get_current_user_info()
    if not has_any_role(claims, ROLE_ADMIN, ROLE_MAINTENANCE):
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    camera = Camera.query.get(camera_id)
    if not camera:
        return jsonify({'success': False, 'message': '摄像头不存在'}), 404
    
    data = request.get_json(silent=True) or {}
    
    # 记录状态
    status_record = CameraStatus(
        camera_id=camera_id,
        status=data.get('status', 1),
        cpu_usage=data.get('cpu_usage'),
        memory_usage=data.get('memory_usage'),
        network_delay=data.get('network_delay'),
        bitrate=data.get('bitrate'),
        fps=data.get('fps')
    )
    
    db.session.add(status_record)
    
    # 更新摄像头主状态
    if 'status' in data:
        camera.status = data['status']
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': '状态更新成功'})
