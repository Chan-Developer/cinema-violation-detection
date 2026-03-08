from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, Alarm, AlarmType, AlarmLevel, Camera, AlarmNotification
from datetime import datetime, timedelta

alarm_bp = Blueprint('alarm', __name__)


def get_current_user_info():
    """获取当前用户信息"""
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    return user_id, claims


@alarm_bp.route('', methods=['GET'])
@jwt_required()
def get_alarms():
    """获取报警列表"""
    _, claims = get_current_user_info()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    camera_id = request.args.get('camera_id', type=int)
    alarm_type = request.args.get('type')
    level = request.args.get('level')
    status = request.args.get('status', type=int)
    cinema_id = request.args.get('cinema_id', type=int)

    # 时间范围
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Alarm.query

    # 根据角色过滤
    if claims.get('role') == 'manager' and claims.get('cinema_id'):
        query = query.join(Camera).filter(Camera.cinema_id == claims.get('cinema_id'))
    elif claims.get('role') == 'operator':
        # 监控员可以看到所有报警
        pass
    elif cinema_id:
        query = query.join(Camera).filter(Camera.cinema_id == cinema_id)
    
    if camera_id:
        query = query.filter(Alarm.camera_id == camera_id)
    if alarm_type:
        query = query.join(AlarmType).filter(AlarmType.code == alarm_type)
    if level:
        query = query.join(AlarmLevel).filter(AlarmLevel.code == level)
    if status is not None:
        query = query.filter(Alarm.status == status)
    if start_date:
        query = query.filter(Alarm.occurred_at >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Alarm.occurred_at <= datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
    
    pagination = query.order_by(Alarm.occurred_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'success': True,
        'alarms': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page
    })


@alarm_bp.route('/<int:alarm_id>', methods=['GET'])
@jwt_required()
def get_alarm(alarm_id):
    """获取报警详情"""
    alarm = Alarm.query.get(alarm_id)
    if not alarm:
        return jsonify({'success': False, 'message': '报警不存在'}), 404
    
    return jsonify({'success': True, 'alarm': alarm.to_dict()})


@alarm_bp.route('/<int:alarm_id>/confirm', methods=['POST'])
@jwt_required()
def confirm_alarm(alarm_id):
    """确认报警"""
    user_id, _ = get_current_user_info()

    alarm = Alarm.query.get(alarm_id)
    if not alarm:
        return jsonify({'success': False, 'message': '报警不存在'}), 404

    if alarm.status != 0:
        return jsonify({'success': False, 'message': '报警已被处理'}), 400

    alarm.status = 1  # 已确认
    alarm.handler_id = user_id
    alarm.confirmed_at = datetime.now()

    db.session.commit()

    return jsonify({'success': True, 'message': '报警已确认', 'alarm': alarm.to_dict()})


@alarm_bp.route('/<int:alarm_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_alarm(alarm_id):
    """处理报警"""
    user_id, _ = get_current_user_info()

    alarm = Alarm.query.get(alarm_id)
    if not alarm:
        return jsonify({'success': False, 'message': '报警不存在'}), 404

    data = request.get_json()

    alarm.status = 2  # 已处理
    alarm.handler_id = user_id
    alarm.handler_note = data.get('note', '')
    alarm.resolved_at = datetime.now()

    db.session.commit()

    return jsonify({'success': True, 'message': '报警已处理', 'alarm': alarm.to_dict()})


@alarm_bp.route('/<int:alarm_id>/ignore', methods=['POST'])
@jwt_required()
def ignore_alarm(alarm_id):
    """忽略报警"""
    user_id, _ = get_current_user_info()

    alarm = Alarm.query.get(alarm_id)
    if not alarm:
        return jsonify({'success': False, 'message': '报警不存在'}), 404

    data = request.get_json()

    alarm.status = 3  # 已忽略
    alarm.handler_id = user_id
    alarm.handler_note = data.get('note', '忽略')
    alarm.resolved_at = datetime.now()

    db.session.commit()

    return jsonify({'success': True, 'message': '报警已忽略', 'alarm': alarm.to_dict()})


@alarm_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_alarm_statistics():
    """获取报警统计"""
    _, claims = get_current_user_info()

    # 时间范围
    days = request.args.get('days', 7, type=int)
    start_date = datetime.now() - timedelta(days=days)

    query = Alarm.query.filter(Alarm.occurred_at >= start_date)

    # 根据角色过滤
    if claims.get('role') == 'manager' and claims.get('cinema_id'):
        query = query.join(Camera).filter(Camera.cinema_id == claims.get('cinema_id'))
    elif claims.get('role') == 'operator':
        pass
    elif claims.get('role') not in ['admin']:
        cinema_id = request.args.get('cinema_id', type=int)
        if cinema_id:
            query = query.join(Camera).filter(Camera.cinema_id == cinema_id)
    
    # 总体统计
    total = query.count()
    pending = query.filter_by(status=0).count()
    confirmed = query.filter_by(status=1).count()
    resolved = query.filter_by(status=2).count()
    ignored = query.filter_by(status=3).count()
    
    # 按类型统计
    type_stats = db.session.query(
        AlarmType.name,
        AlarmType.code,
        db.func.count(Alarm.id)
    ).join(Alarm, Alarm.alarm_type_id == AlarmType.id).filter(
        Alarm.occurred_at >= start_date
    ).group_by(AlarmType.id).all()
    
    # 按级别统计
    level_stats = db.session.query(
        AlarmLevel.name,
        AlarmLevel.code,
        AlarmLevel.color,
        db.func.count(Alarm.id)
    ).join(Alarm, Alarm.level_id == AlarmLevel.id).filter(
        Alarm.occurred_at >= start_date
    ).group_by(AlarmLevel.id).all()
    
    # 按日期统计
    date_stats = db.session.query(
        db.func.date(Alarm.occurred_at).label('date'),
        db.func.count(Alarm.id)
    ).filter(Alarm.occurred_at >= start_date).group_by(
        db.func.date(Alarm.occurred_at)
    ).all()
    
    return jsonify({
        'success': True,
        'summary': {
            'total': total,
            'pending': pending,
            'confirmed': confirmed,
            'resolved': resolved,
            'ignored': ignored
        },
        'by_type': [{'name': t[0], 'code': t[1], 'count': t[2]} for t in type_stats],
        'by_level': [{'name': l[0], 'code': l[1], 'color': l[2], 'count': l[3]} for l in level_stats],
        'by_date': [{'date': str(d[0]), 'count': d[1]} for d in date_stats]
    })


@alarm_bp.route('/types', methods=['GET'])
@jwt_required()
def get_alarm_types():
    """获取报警类型"""
    types = AlarmType.query.all()
    return jsonify({
        'success': True,
        'types': [{'id': t.id, 'name': t.name, 'code': t.code, 'description': t.description, 'icon': t.icon} for t in types]
    })


@alarm_bp.route('/levels', methods=['GET'])
@jwt_required()
def get_alarm_levels():
    """获取报警级别"""
    levels = AlarmLevel.query.order_by(AlarmLevel.priority).all()
    return jsonify({
        'success': True,
        'levels': [{'id': l.id, 'name': l.name, 'code': l.code, 'color': l.color, 'priority': l.priority} for l in levels]
    })


@alarm_bp.route('/pending/count', methods=['GET'])
@jwt_required()
def get_pending_count():
    """获取待处理报警数量"""
    identity = get_jwt_identity()
    
    query = Alarm.query.filter_by(status=0)
    
    if identity['role'] == 'manager' and identity.get('cinema_id'):
        query = query.join(Camera).filter(Camera.cinema_id == identity['cinema_id'])
    
    count = query.count()
    
    return jsonify({'success': True, 'count': count})
