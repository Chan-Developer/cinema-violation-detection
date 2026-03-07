from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Cinema, Hall, Camera, Alarm, AlarmType, AlarmLevel, User
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """获取总览数据"""
    identity = get_jwt_identity()
    
    # 基础统计
    total_cinemas = Cinema.query.count()
    total_halls = Hall.query.count()
    total_cameras = Camera.query.count()
    online_cameras = Camera.query.filter_by(status=1).count()
    
    # 今日报警
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    alarm_query = Alarm.query.filter(Alarm.occurred_at >= today_start)
    
    today_alarms = alarm_query.count()
    pending_alarms = alarm_query.filter_by(status=0).count()
    
    # 今日报警类型分布
    alarm_by_type = db.session.query(
        AlarmType.name,
        func.count(Alarm.id)
    ).join(Alarm, Alarm.alarm_type_id == AlarmType.id).filter(
        Alarm.occurred_at >= today_start
    ).group_by(AlarmType.id).all()
    
    # 最近7天报警趋势
    week_ago = datetime.now() - timedelta(days=7)
    trend = db.session.query(
        func.date(Alarm.occurred_at).label('date'),
        func.count(Alarm.id)
    ).filter(Alarm.occurred_at >= week_ago).group_by(
        func.date(Alarm.occurred_at)
    ).all()
    
    return jsonify({
        'success': True,
        'data': {
            'cinemas': total_cinemas,
            'halls': total_halls,
            'cameras': {
                'total': total_cameras,
                'online': online_cameras,
                'offline': total_cameras - online_cameras
            },
            'alarms': {
                'today': today_alarms,
                'pending': pending_alarms
            },
            'alarm_types': [{'name': t[0], 'count': t[1]} for t in alarm_by_type],
            'alarm_trend': [{'date': str(t[0]), 'count': t[1]} for t in trend]
        }
    })


@dashboard_bp.route('/cinema/<int:cinema_id>', methods=['GET'])
@jwt_required()
def get_cinema_dashboard(cinema_id):
    """获取影院仪表盘"""
    cinema = Cinema.query.get(cinema_id)
    if not cinema:
        return jsonify({'success': False, 'message': '影院不存在'}), 404
    
    # 影厅数量
    halls = Hall.query.filter_by(cinema_id=cinema_id).all()
    hall_count = len(halls)
    
    # 摄像头数量
    cameras = Camera.query.filter_by(cinema_id=cinema_id).all()
    camera_count = len(cameras)
    online_cameras = sum(1 for c in cameras if c.status == 1)
    
    # 今日报警
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    alarm_query = Alarm.query.join(Camera).filter(
        Camera.cinema_id == cinema_id,
        Alarm.occurred_at >= today_start
    )
    
    today_alarms = alarm_query.count()
    pending_alarms = alarm_query.filter_by(status=0).count()
    
    # 各影厅报警统计
    hall_alarms = db.session.query(
        Hall.name,
        func.count(Alarm.id)
    ).join(Camera, Camera.hall_id == Hall.id).join(Alarm, Alarm.camera_id == Camera.id).filter(
        Hall.cinema_id == cinema_id,
        Alarm.occurred_at >= today_start
    ).group_by(Hall.id).all()
    
    return jsonify({
        'success': True,
        'data': {
            'cinema': cinema.to_dict(),
            'halls': hall_count,
            'cameras': {
                'total': camera_count,
                'online': online_cameras,
                'offline': camera_count - online_cameras
            },
            'alarms': {
                'today': today_alarms,
                'pending': pending_alarms
            },
            'hall_alarms': [{'name': h[0], 'count': h[1]} for h in hall_alarms]
        }
    })


@dashboard_bp.route('/alarms/recent', methods=['GET'])
@jwt_required()
def get_recent_alarms():
    """获取最近报警"""
    identity = get_jwt_identity()
    
    limit = request.args.get('limit', 10, type=int)
    
    query = Alarm.query.order_by(Alarm.occurred_at.desc()).limit(limit)
    
    if identity['role'] == 'manager' and identity.get('cinema_id'):
        query = query.join(Camera).filter(Camera.cinema_id == identity['cinema_id'])
    
    alarms = query.all()
    
    return jsonify({
        'success': True,
        'alarms': [a.to_dict() for a in alarms]
    })


@dashboard_bp.route('/cameras/status', methods=['GET'])
@jwt_required()
def get_cameras_status():
    """获取所有摄像头状态"""
    identity = get_jwt_identity()
    
    query = Camera.query
    
    if identity['role'] == 'manager' and identity.get('cinema_id'):
        query = query.filter(Camera.cinema_id == identity['cinema_id'])
    
    cameras = query.all()
    
    status_summary = {
        'online': 0,
        'offline': 0,
        'maintenance': 0
    }
    
    camera_list = []
    for camera in cameras:
        camera_list.append({
            'id': camera.id,
            'name': camera.name,
            'cinema_name': camera.cinema.name if camera.cinema else None,
            'hall_name': camera.hall.name if camera.hall else None,
            'position': camera.position,
            'status': camera.status,
            'stream_status': camera.stream_status
        })
        
        if camera.status == 1:
            status_summary['online'] += 1
        elif camera.status == 2:
            status_summary['maintenance'] += 1
        else:
            status_summary['offline'] += 1
    
    return jsonify({
        'success': True,
        'cameras': camera_list,
        'summary': status_summary
    })
