from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, Role

role_bp = Blueprint('role', __name__)


def get_current_user_info():
    """获取当前用户信息"""
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    return user_id, claims


@role_bp.route('', methods=['GET'])
@jwt_required()
def get_roles():
    """获取角色列表"""
    roles = Role.query.all()
    return jsonify({
        'success': True,
        'roles': [r.to_dict() if hasattr(r, 'to_dict') else {
            'id': r.id,
            'name': r.name,
            'description': r.description
        } for r in roles]
    })


@role_bp.route('/<int:role_id>', methods=['GET'])
@jwt_required()
def get_role(role_id):
    """获取角色详情"""
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'success': False, 'message': '角色不存在'}), 404

    role_dict = role.to_dict() if hasattr(role, 'to_dict') else {
        'id': role.id,
        'name': role.name,
        'description': role.description
    }
    return jsonify({'success': True, 'role': role_dict})


@role_bp.route('', methods=['POST'])
@jwt_required()
def create_role():
    """创建角色"""
    _, claims = get_current_user_info()
    if claims.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403

    data = request.get_json()
    name = data.get('name')
    description = data.get('description')

    if not name:
        return jsonify({'success': False, 'message': '角色名称不能为空'}), 400

    # 检查角色是否已存在
    if Role.query.filter_by(name=name).first():
        return jsonify({'success': False, 'message': '角色已存在'}), 400

    role = Role(
        name=name,
        description=description or ''
    )

    db.session.add(role)
    db.session.commit()

    role_dict = role.to_dict() if hasattr(role, 'to_dict') else {
        'id': role.id,
        'name': role.name,
        'description': role.description
    }
    return jsonify({'success': True, 'message': '角色创建成功', 'role': role_dict})


@role_bp.route('/<int:role_id>', methods=['PUT'])
@jwt_required()
def update_role(role_id):
    """更新角色"""
    _, claims = get_current_user_info()
    if claims.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403

    role = Role.query.get(role_id)
    if not role:
        return jsonify({'success': False, 'message': '角色不存在'}), 404

    data = request.get_json()

    if 'name' in data:
        # 检查名称是否被修改
        if data['name'] != role.name:
            # 检查新名称是否被占用
            existing = Role.query.filter_by(name=data['name']).first()
            if existing:
                return jsonify({'success': False, 'message': '角色名称已存在'}), 400
        role.name = data['name']

    if 'description' in data:
        role.description = data['description']

    db.session.commit()

    role_dict = role.to_dict() if hasattr(role, 'to_dict') else {
        'id': role.id,
        'name': role.name,
        'description': role.description
    }
    return jsonify({'success': True, 'message': '角色更新成功', 'role': role_dict})


@role_bp.route('/<int:role_id>', methods=['DELETE'])
@jwt_required()
def delete_role(role_id):
    """删除角色"""
    _, claims = get_current_user_info()
    if claims.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403

    role = Role.query.get(role_id)
    if not role:
        return jsonify({'success': False, 'message': '角色不存在'}), 404

    # 检查是否有用户使用该角色
    user_count = role.users.count() if hasattr(role, 'users') else 0
    if user_count > 0:
        return jsonify({'success': False, 'message': '该角色已被用户使用，无法删除'}), 400

    db.session.delete(role)
    db.session.commit()

    return jsonify({'success': True, 'message': '角色删除成功'})
