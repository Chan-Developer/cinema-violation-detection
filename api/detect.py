from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import db
from config import config
from services.detection import DetectionWorker
import os
import cv2
import base64
from io import BytesIO

detect_bp = Blueprint('detect', __name__)

ALLOWED_EXTENSIONS = config['development'].ALLOWED_IMAGE | config['development'].ALLOWED_VIDEO


def allowed_file(filename):
    """检查文件是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def is_image(filename):
    """检查是否为图片"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ext in config['development'].ALLOWED_IMAGE


@detect_bp.route('/detect', methods=['POST'])
@jwt_required()
def detect_image():
    """
    上传图片进行检测
    ---
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: 要检测的图片文件
    responses:
      200:
        description: 检测成功
        schema:
          properties:
            success:
              type: boolean
            detections:
              type: array
              items:
                properties:
                  class:
                    type: string
                  confidence:
                    type: number
                  bbox:
                    type: array
            annotated_image:
              type: string
              description: base64编码的标注图片
            llm_description:
              type: string
              description: LLM生成的图片描述
    """
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有找到文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': '不支持的文件格式'}), 400

        if file.content_length > 200 * 1024 * 1024:
            return jsonify({'success': False, 'message': '文件大小超过200MB'}), 400

        # 保存文件
        filename = secure_filename(file.filename)
        upload_dir = config['development'].UPLOAD_FOLDER
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        # 读取图片
        if not is_image(filename):
            # 如果是视频，提取第一帧
            cap = cv2.VideoCapture(filepath)
            ret, frame = cap.read()
            cap.release()
            if not ret:
                return jsonify({'success': False, 'message': '无法读取视频文件'}), 400
        else:
            frame = cv2.imread(filepath)
            if frame is None:
                return jsonify({'success': False, 'message': '无法读取图片文件'}), 400

        # 执行检测
        worker = DetectionWorker(camera_id=0, detection_types='person,car,dog,cat,phone')
        detections = worker._detect(frame)

        # 绘制检测框
        annotated_frame = frame.copy()
        for detection in detections:
            x1, y1, x2, y2 = detection['box']
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{detection['type']}: {detection['confidence']:.2f}"
            cv2.putText(annotated_frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 编码为base64
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        # 尝试使用LLM获取描述
        llm_description = None
        try:
            from utils.llm import call_llm_api, generate_local_description
            # 即使没有检测到任何物体，也生成描述
            llm_description = call_llm_api(detections, filepath)
        except Exception as e:
            print(f"LLM描述API失败: {e}")
            # 使用本地生成的描述作为备选方案
            try:
                from utils.llm import generate_local_description
                llm_description = generate_local_description(detections)
            except:
                llm_description = "检测完成，描述生成失败"

        # 清理
        if os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({
            'success': True,
            'detections': detections,
            'annotated_image': f'data:image/jpeg;base64,{img_base64}',
            'llm_description': llm_description or '暂无描述'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


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
