from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
from models import VideoRecognitionResult
from config import config
from services.video_detection import video_detection_manager
from utils.roles import apply_manager_scope, is_admin
import os
import uuid

detect_bp = Blueprint('detect', __name__)

ALLOWED_EXTENSIONS = config['development'].ALLOWED_VIDEO
MAX_UPLOAD_SIZE = 200 * 1024 * 1024


def allowed_file(filename):
    """检查文件是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _upload_dir():
    path = config['development'].UPLOAD_FOLDER
    os.makedirs(path, exist_ok=True)
    return path


def _is_too_large(file_storage):
    size = file_storage.content_length
    if size is None:
        size = request.content_length
    return bool(size and size > MAX_UPLOAD_SIZE)


def _clamp_confidence_threshold(raw_value, default=0.35):
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        value = default
    return max(0.1, min(0.9, value))


@detect_bp.route('/detect/video', methods=['POST'])
@jwt_required()
def detect_video_upload():
    """上传视频并异步识别（每隔N帧采样，YOLO检人后交由大模型判断）"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有找到文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': '不支持的文件格式'}), 400

        if _is_too_large(file):
            return jsonify({'success': False, 'message': '文件大小超过200MB'}), 400

        frame_interval = request.form.get('frame_interval', 90, type=int)
        camera_id = request.form.get('camera_id', type=int)
        cinema_id = request.form.get('cinema_id', type=int)
        detection_types = request.form.get('detection_types', '', type=str)
        alarm_window_seconds = request.form.get('alarm_window_seconds', 60, type=int)
        alarm_threshold = request.form.get('alarm_threshold', 3, type=int)
        alarm_cooldown_seconds = request.form.get('alarm_cooldown_seconds', type=int)
        confidence_threshold = _clamp_confidence_threshold(request.form.get('confidence_threshold'))

        cinema_id = apply_manager_scope(claims, cinema_id)

        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(_upload_dir(), unique_name)
        file.save(filepath)

        task_id = video_detection_manager.start_task(
            app=current_app._get_current_object(),
            video_path=filepath,
            camera_id=camera_id,
            cinema_id=cinema_id,
            detection_types=detection_types,
            frame_interval=frame_interval,
            confidence_threshold=confidence_threshold,
            created_by=user_id,
            alarm_window_seconds=alarm_window_seconds,
            alarm_threshold=alarm_threshold,
            alarm_cooldown_seconds=alarm_cooldown_seconds
        )

        return jsonify({
            'success': True,
            'message': '视频识别任务已创建',
            'task_id': task_id,
            'confidence_threshold': confidence_threshold,
            'alarm_policy': {
                'window_seconds': max(1, int(alarm_window_seconds or 60)),
                'threshold': max(1, int(alarm_threshold or 3)),
                'cooldown_seconds': (
                    max(1, int(alarm_cooldown_seconds))
                    if alarm_cooldown_seconds is not None
                    else max(1, int(alarm_window_seconds or 60))
                ),
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@detect_bp.route('/detect/video/tasks/<string:task_id>', methods=['GET'])
@jwt_required()
def get_video_task(task_id):
    """查询视频检测任务状态"""
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    task = video_detection_manager.get_task(task_id)
    if not task:
        records = VideoRecognitionResult.query.filter_by(task_id=task_id).order_by(
            VideoRecognitionResult.frame_index.asc()
        ).all()
        if not records:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        violation_frames = sum(1 for r in records if r.violation)
        task = {
            'task_id': task_id,
            'status': 'completed',
            'message': '任务状态缓存已丢失，已从识别记录恢复',
            'progress': 100,
            'frame_interval': None,
            'camera_id': records[0].camera_id,
            'cinema_id': records[0].cinema_id,
            'created_by': None,
            'video_path': None,
            'total_frames': 0,
            'processed_frames': 0,
            'sampled_frames': len(records),
            'hit_samples': sum(1 for r in records if (r.person_count or 0) > 0),
            'records_saved': len(records),
            'violation_frames': violation_frames,
            'samples': [],
            'summary': f'已恢复{len(records)}条识别记录，违规帧{violation_frames}条。',
            'created_at': records[0].created_at.isoformat() if records[0].created_at else None,
            'updated_at': records[-1].created_at.isoformat() if records[-1].created_at else None,
            'finished_at': records[-1].created_at.isoformat() if records[-1].created_at else None,
        }

    created_by = task.get('created_by')
    if created_by and created_by != user_id and not is_admin(claims):
        return jsonify({'success': False, 'message': '无权查看该任务'}), 403

    return jsonify({'success': True, 'task': task})


@detect_bp.route('/detect/video/tasks/<string:task_id>/results', methods=['GET'])
@jwt_required()
def get_video_task_results(task_id):
    """查询视频识别结果（持久化）"""
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    task = video_detection_manager.get_task(task_id)
    if task:
        created_by = task.get('created_by')
        if created_by and created_by != user_id and not is_admin(claims):
            return jsonify({'success': False, 'message': '无权查看该任务'}), 403

    records = VideoRecognitionResult.query.filter_by(task_id=task_id).order_by(
        VideoRecognitionResult.frame_index.asc()
    ).all()
    return jsonify({
        'success': True,
        'task_id': task_id,
        'total': len(records),
        'results': [r.to_dict() for r in records]
    })


@detect_bp.route('/detect/status/<int:camera_id>', methods=['GET'])
@jwt_required()
def get_detection_status(camera_id):
    """获取指定摄像头的检测状态"""
    try:
        from services.detection import detection_service
        status = detection_service.get_status(camera_id)
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@detect_bp.route('/detect/start/<int:camera_id>', methods=['POST'])
@jwt_required()
def start_detection(camera_id):
    """启动指定摄像头的检测"""
    try:
        from services.detection import detection_service
        result = detection_service.start_detection(camera_id)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@detect_bp.route('/detect/stop/<int:camera_id>', methods=['POST'])
@jwt_required()
def stop_detection(camera_id):
    """停止指定摄像头的检测"""
    try:
        from services.detection import detection_service
        result = detection_service.stop_detection(camera_id)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
