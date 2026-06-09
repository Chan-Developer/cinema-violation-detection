import os
import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from config import config
from models import Camera, Cinema, MobileEvidence, db
from utils.roles import apply_manager_scope, is_admin, manager_cinema_id


evidence_bp = Blueprint('evidence', __name__)

ALLOWED_IMAGE_EXTENSIONS = config['development'].ALLOWED_IMAGE
MAX_EVIDENCE_SIZE = 20 * 1024 * 1024


def _evidence_dir():
    path = os.path.join(config['development'].UPLOAD_FOLDER, 'evidence')
    os.makedirs(path, exist_ok=True)
    return path


def _allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def _is_too_large(file_storage):
    size = file_storage.content_length or request.content_length
    return bool(size and size > MAX_EVIDENCE_SIZE)


@evidence_bp.route('/mobile', methods=['POST'])
@jwt_required()
def upload_mobile_evidence():
    """手机端拍照上传留证，只负责保存现场证据，不直接触发告警。"""
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有找到图片'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'message': '文件名为空'}), 400
    if not _allowed_image(file.filename):
        return jsonify({'success': False, 'message': '仅支持图片格式'}), 400
    if _is_too_large(file):
        return jsonify({'success': False, 'message': '图片大小不能超过20MB'}), 400

    camera_id = request.form.get('camera_id', type=int)
    cinema_id = request.form.get('cinema_id', type=int)
    note = (request.form.get('note') or '').strip()
    location_text = (request.form.get('location_text') or '').strip()

    if camera_id:
        camera = Camera.query.get(camera_id)
        if not camera:
            return jsonify({'success': False, 'message': '摄像头不存在'}), 404
        scoped_cinema_id = manager_cinema_id(claims)
        if scoped_cinema_id and scoped_cinema_id != camera.cinema_id:
            return jsonify({'success': False, 'message': '仅可上传所属影院留证'}), 403
        cinema_id = camera.cinema_id
    else:
        cinema_id = apply_manager_scope(claims, cinema_id)

    if cinema_id and not Cinema.query.get(cinema_id):
        return jsonify({'success': False, 'message': '影院不存在'}), 404

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(_evidence_dir(), unique_name)
    file.save(filepath)

    evidence = MobileEvidence(
        user_id=user_id,
        cinema_id=cinema_id,
        camera_id=camera_id,
        image_url=f"/static/uploads/evidence/{unique_name}",
        note=note,
        location_text=location_text,
    )
    db.session.add(evidence)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '留证上传成功',
        'evidence': evidence.to_dict()
    })


@evidence_bp.route('/mobile', methods=['GET'])
@jwt_required()
def list_mobile_evidences():
    """获取手机端留证记录，管理员看全部，其他角色看自己或所属影院。"""
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    query = MobileEvidence.query
    scoped_cinema_id = manager_cinema_id(claims)
    if scoped_cinema_id:
        query = query.filter(MobileEvidence.cinema_id == scoped_cinema_id)
    elif not is_admin(claims):
        query = query.filter(MobileEvidence.user_id == user_id)

    pagination = query.order_by(MobileEvidence.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return jsonify({
        'success': True,
        'evidences': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages,
    })
