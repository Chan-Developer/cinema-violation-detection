from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, Camera, VideoStream
from services.video_stream import stream_manager

stream_bp = Blueprint('stream', __name__)


def get_current_user_info():
    """获取当前用户信息"""
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    return user_id, claims


@stream_bp.route('/<int:camera_id>/start', methods=['POST'])
@jwt_required()
def start_stream(camera_id):
    """启动视频流"""
    _, claims = get_current_user_info()
    if claims.get('role') not in ['admin', 'manager', 'operator', 'maintenance']:
        return jsonify({'success': False, 'message': '权限不足'}), 403

    result = stream_manager.start_stream(camera_id)
    return jsonify(result)


@stream_bp.route('/<int:camera_id>/stop', methods=['POST'])
@jwt_required()
def stop_stream(camera_id):
    """停止视频流"""
    _, claims = get_current_user_info()
    if claims.get('role') not in ['admin', 'manager', 'operator', 'maintenance']:
        return jsonify({'success': False, 'message': '权限不足'}), 403

    result = stream_manager.stop_stream(camera_id)
    return jsonify(result)


@stream_bp.route('/<int:camera_id>/status', methods=['GET'])
@jwt_required()
def get_stream_status(camera_id):
    """获取视频流状态"""
    status = stream_manager.get_stream_status(camera_id)
    return jsonify({'success': True, 'status': status})


@stream_bp.route('/<int:camera_id>/frame', methods=['GET'])
@jwt_required()
def get_frame(camera_id):
    """获取当前帧"""
    frame_data = stream_manager.get_frame(camera_id)
    if frame_data:
        import base64
        frame_b64 = base64.b64encode(frame_data['frame_data']).decode('utf-8')
        return jsonify({
            'success': True,
            'frame': f'data:image/jpeg;base64,{frame_b64}',
            'frame_id': frame_data['frame_id'],
            'timestamp': frame_data['timestamp']
        })
    return jsonify({'success': False, 'message': '无帧数据'})


@stream_bp.route('/all/status', methods=['GET'])
@jwt_required()
def get_all_stream_status():
    """获取所有流状态"""
    cameras = Camera.query.all()
    status_list = []
    for camera in cameras:
        status = stream_manager.get_stream_status(camera.id)
        status_list.append({
            'camera_id': camera.id,
            'camera_name': camera.name,
            **status
        })
    return jsonify({'success': True, 'streams': status_list})
