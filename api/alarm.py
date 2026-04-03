from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import (
    db, Alarm, AlarmType, AlarmLevel, Camera, AlarmActionLog,
    ALARM_STATUS_PENDING, ALARM_STATUS_CONFIRMED, ALARM_STATUS_PROCESSING,
    ALARM_STATUS_RESOLVED, ALARM_STATUS_IGNORED
)
from datetime import datetime, timedelta
from utils.roles import (
    is_admin,
    is_operator,
    manager_cinema_id,
)

alarm_bp = Blueprint('alarm', __name__)


def get_current_user_info():
    """获取当前用户信息"""
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    return user_id, claims


def add_action_log(alarm_id, action, user_id=None, from_status=None, to_status=None, note=''):
    """记录报警状态流转留痕"""
    log = AlarmActionLog(
        alarm_id=alarm_id,
        user_id=user_id,
        action=action,
        from_status=from_status,
        to_status=to_status,
        note=note
    )
    db.session.add(log)


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
    scoped_cinema_id = manager_cinema_id(claims)
    if scoped_cinema_id:
        query = query.join(Camera).filter(Camera.cinema_id == scoped_cinema_id)
    elif is_operator(claims):
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

    if alarm.status != ALARM_STATUS_PENDING:
        return jsonify({'success': False, 'message': '报警已被处理'}), 400

    from_status = alarm.status
    alarm.status = ALARM_STATUS_CONFIRMED
    alarm.handler_id = user_id
    alarm.confirmed_at = datetime.now()
    add_action_log(
        alarm.id, 'confirm', user_id=user_id,
        from_status=from_status, to_status=alarm.status, note='报警已确认'
    )

    db.session.commit()

    return jsonify({'success': True, 'message': '报警已确认', 'alarm': alarm.to_dict()})


@alarm_bp.route('/<int:alarm_id>/process', methods=['POST'])
@jwt_required()
def process_alarm(alarm_id):
    """进入处理中"""
    user_id, _ = get_current_user_info()

    alarm = Alarm.query.get(alarm_id)
    if not alarm:
        return jsonify({'success': False, 'message': '报警不存在'}), 404

    if alarm.status != ALARM_STATUS_CONFIRMED:
        return jsonify({'success': False, 'message': '仅已确认报警可进入处理中'}), 400

    data = request.get_json(silent=True) or {}
    from_status = alarm.status
    alarm.status = ALARM_STATUS_PROCESSING
    alarm.handler_id = user_id
    alarm.handler_note = data.get('note', alarm.handler_note)
    add_action_log(
        alarm.id, 'process', user_id=user_id,
        from_status=from_status, to_status=alarm.status, note=data.get('note', '进入处理中')
    )

    db.session.commit()

    return jsonify({'success': True, 'message': '报警处理中', 'alarm': alarm.to_dict()})


@alarm_bp.route('/<int:alarm_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_alarm(alarm_id):
    """处理报警"""
    user_id, _ = get_current_user_info()

    alarm = Alarm.query.get(alarm_id)
    if not alarm:
        return jsonify({'success': False, 'message': '报警不存在'}), 404

    if alarm.status not in [ALARM_STATUS_CONFIRMED, ALARM_STATUS_PROCESSING]:
        return jsonify({'success': False, 'message': '仅已确认/处理中报警可处理完成'}), 400

    data = request.get_json(silent=True) or {}

    from_status = alarm.status
    alarm.status = ALARM_STATUS_RESOLVED
    alarm.handler_id = user_id
    alarm.handler_note = data.get('note', '')
    alarm.resolved_at = datetime.now()
    add_action_log(
        alarm.id, 'resolve', user_id=user_id,
        from_status=from_status, to_status=alarm.status, note=data.get('note', '报警已处理')
    )

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

    if alarm.status in [ALARM_STATUS_RESOLVED, ALARM_STATUS_IGNORED]:
        return jsonify({'success': False, 'message': '报警已结束，无法忽略'}), 400

    data = request.get_json(silent=True) or {}

    from_status = alarm.status
    alarm.status = ALARM_STATUS_IGNORED
    alarm.handler_id = user_id
    alarm.handler_note = data.get('note', '忽略')
    alarm.resolved_at = datetime.now()
    add_action_log(
        alarm.id, 'ignore', user_id=user_id,
        from_status=from_status, to_status=alarm.status, note=alarm.handler_note
    )

    db.session.commit()

    return jsonify({'success': True, 'message': '报警已忽略', 'alarm': alarm.to_dict()})


@alarm_bp.route('/<int:alarm_id>/logs', methods=['GET'])
@jwt_required()
def get_alarm_logs(alarm_id):
    """获取报警留痕日志"""
    alarm = Alarm.query.get(alarm_id)
    if not alarm:
        return jsonify({'success': False, 'message': '报警不存在'}), 404

    logs = alarm.action_logs.order_by(AlarmActionLog.created_at.asc()).all()
    return jsonify({'success': True, 'logs': [log.to_dict() for log in logs]})


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
    scoped_cinema_id = manager_cinema_id(claims)
    if scoped_cinema_id:
        query = query.join(Camera).filter(Camera.cinema_id == scoped_cinema_id)
    elif is_operator(claims):
        pass
    elif not is_admin(claims):
        cinema_id = request.args.get('cinema_id', type=int)
        if cinema_id:
            query = query.join(Camera).filter(Camera.cinema_id == cinema_id)
    
    # 总体统计
    total = query.count()
    pending = query.filter_by(status=ALARM_STATUS_PENDING).count()
    confirmed = query.filter_by(status=ALARM_STATUS_CONFIRMED).count()
    processing = query.filter_by(status=ALARM_STATUS_PROCESSING).count()
    resolved = query.filter_by(status=ALARM_STATUS_RESOLVED).count()
    ignored = query.filter_by(status=ALARM_STATUS_IGNORED).count()
    
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
            'processing': processing,
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
    _, claims = get_current_user_info()
    
    query = Alarm.query.filter(Alarm.status.in_([
        ALARM_STATUS_PENDING,
        ALARM_STATUS_CONFIRMED,
        ALARM_STATUS_PROCESSING
    ]))
    
    scoped_cinema_id = manager_cinema_id(claims)
    if scoped_cinema_id:
        query = query.join(Camera).filter(Camera.cinema_id == scoped_cinema_id)
    
    count = query.count()
    
    return jsonify({'success': True, 'count': count})
