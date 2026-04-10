from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from models import db, User, Role
from datetime import datetime
from utils.roles import (
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_OPERATOR,
    ROLE_MAINTENANCE,
    SYSTEM_ROLE_ORDER,
    SYSTEM_ROLE_META,
    is_admin,
    is_manager,
    manager_cinema_id,
)

auth_bp = Blueprint('auth', __name__)


def get_current_user_with_claims():
    """获取当前用户和claims信息（用于权限检查）

    Returns:
        tuple: (user_id: int, claims: dict)
    """
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    return user_id, claims


def can_manage_users(claims):
    return is_admin(claims) or is_manager(claims)


def manager_scope_or_none(claims):
    if not is_manager(claims):
        return None
    return manager_cinema_id(claims)


def role_by_id_or_none(role_id):
    if not role_id:
        return None
    return Role.query.get(role_id)


def manager_can_assign_role(role_name):
    return role_name in {ROLE_OPERATOR, ROLE_MAINTENANCE}


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
    
    if user.status == 0:
        return jsonify({'success': False, 'message': '账号已被禁用'}), 403
    
    # 更新最后登录时间
    user.last_login = datetime.now()
    db.session.commit()

    # 生成Token
    # identity 是用户ID（必须是字符串）
    # additional_claims 是额外信息
    additional_claims = {
        'role': user.role.name if user.role else None,
        'role_id': user.role_id,
        'cinema_id': user.cinema_id
    }
    access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=str(user.id), additional_claims=additional_claims)
    
    return jsonify({
        'success': True,
        'message': '登录成功',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    })


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新Token"""
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({'success': True, 'access_token': access_token})


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前用户信息"""
    user_id, _ = get_current_user_with_claims()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    return jsonify({'success': True, 'user': user.to_dict()})


@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """获取用户列表"""
    _, claims = get_current_user_with_claims()
    if not can_manage_users(claims):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role = request.args.get('role')
    cinema_id = request.args.get('cinema_id', type=int)
    keyword = request.args.get('keyword')

    query = User.query.join(Role, User.role_id == Role.id)

    scoped_cinema_id = manager_scope_or_none(claims)
    if scoped_cinema_id is not None:
        query = query.filter(User.cinema_id == scoped_cinema_id).filter(Role.name != ROLE_ADMIN)

    if role:
        query = query.filter(Role.name == role)
    if cinema_id:
        query = query.filter(User.cinema_id == cinema_id)
    if keyword:
        query = query.filter(
            (User.username.contains(keyword)) |
            (User.real_name.contains(keyword)) |
            (User.email.contains(keyword))
        )

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'success': True,
        'users': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page
    })


@auth_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    """创建用户"""
    _, claims = get_current_user_with_claims()
    if not can_manage_users(claims):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')
    role_id = data.get('role_id')

    if not username or not password or not role_id:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': '用户名已存在'}), 400

    role = role_by_id_or_none(role_id)
    if not role:
        return jsonify({'success': False, 'message': '角色不存在'}), 400

    cinema_id = data.get('cinema_id')
    scoped_cinema_id = manager_scope_or_none(claims)
    if scoped_cinema_id is not None:
        if not manager_can_assign_role(role.name):
            return jsonify({'success': False, 'message': '影院经理仅可创建监控员/运维账号'}), 403
        cinema_id = scoped_cinema_id

    new_user = User(
        username=username,
        real_name=data.get('real_name'),
        email=data.get('email'),
        phone=data.get('phone'),
        role_id=role_id,
        cinema_id=cinema_id,
        status=1
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'success': True, 'message': '用户创建成功', 'user': new_user.to_dict()})


@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户"""
    current_user_id, claims = get_current_user_with_claims()
    if not can_manage_users(claims):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    if is_manager(claims):
        scoped_cinema_id = manager_scope_or_none(claims)
        if scoped_cinema_id is None:
            return jsonify({'success': False, 'message': '影院经理未绑定影院，无法管理用户'}), 403
        if user.cinema_id != scoped_cinema_id:
            return jsonify({'success': False, 'message': '仅可管理所属影院用户'}), 403
        if user.role and user.role.name in {ROLE_ADMIN, ROLE_MANAGER}:
            return jsonify({'success': False, 'message': '影院经理不能修改管理员/经理账号'}), 403

    data = request.get_json(silent=True) or {}

    # 检查用户名是否被修改，如果被修改则检查是否重复
    if 'username' in data and data['username'] != user.username:
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        user.username = data['username']

    if 'real_name' in data:
        user.real_name = data['real_name']
    if 'email' in data:
        user.email = data['email']
    if 'phone' in data:
        user.phone = data['phone']
    if 'role_id' in data:
        target_role = role_by_id_or_none(data['role_id'])
        if not target_role:
            return jsonify({'success': False, 'message': '角色不存在'}), 400
        if is_manager(claims) and not manager_can_assign_role(target_role.name):
            return jsonify({'success': False, 'message': '影院经理仅可分配监控员/运维角色'}), 403
        user.role_id = data['role_id']
    if 'cinema_id' in data:
        if is_manager(claims):
            user.cinema_id = manager_scope_or_none(claims)
        else:
            user.cinema_id = data['cinema_id']
    if 'status' in data:
        user.status = data['status']
    if 'password' in data and data['password']:
        user.set_password(data['password'])

    db.session.commit()

    return jsonify({'success': True, 'message': '用户更新成功', 'user': user.to_dict()})


@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """删除用户"""
    current_user_id, claims = get_current_user_with_claims()
    if not can_manage_users(claims):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    if user.id == current_user_id:
        return jsonify({'success': False, 'message': '不能删除自己的账号'}), 400

    if is_manager(claims):
        scoped_cinema_id = manager_scope_or_none(claims)
        if scoped_cinema_id is None:
            return jsonify({'success': False, 'message': '影院经理未绑定影院，无法管理用户'}), 403
        if user.cinema_id != scoped_cinema_id:
            return jsonify({'success': False, 'message': '仅可删除所属影院用户'}), 403
        if user.role and user.role.name in {ROLE_ADMIN, ROLE_MANAGER}:
            return jsonify({'success': False, 'message': '影院经理不能删除管理员/经理账号'}), 403

    db.session.delete(user)
    db.session.commit()

    return jsonify({'success': True, 'message': '用户删除成功'})


@auth_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_roles():
    """获取角色列表"""
    roles = Role.query.all()
    roles_sorted = sorted(
        roles,
        key=lambda item: (
            SYSTEM_ROLE_ORDER.index(item.name)
            if item.name in SYSTEM_ROLE_ORDER
            else len(SYSTEM_ROLE_ORDER),
            item.id
        )
    )
    _, claims = get_current_user_with_claims()
    if is_manager(claims):
        roles_sorted = [r for r in roles_sorted if r.name in {ROLE_OPERATOR, ROLE_MAINTENANCE}]

    return jsonify({
        'success': True,
        'roles': [{'id': r.id, 'name': r.name, 'description': r.description} for r in roles_sorted]
    })


@auth_bp.route('/role-relations', methods=['GET'])
@jwt_required()
def get_role_relations():
    """返回统一角色关系定义，供前后端对齐显示与权限解释"""
    _, claims = get_current_user_with_claims()
    return jsonify({
        'success': True,
        'current_role': claims.get('role'),
        'current_cinema_scope': manager_cinema_id(claims),
        'roles': [SYSTEM_ROLE_META[name] for name in SYSTEM_ROLE_ORDER if name in SYSTEM_ROLE_META],
        'rules': {
            'manager_scope': 'manager 角色始终绑定 token.cinema_id，不能跨影院操作',
            'admin_scope': 'admin 可跨影院操作并管理用户、角色与影院',
            'operator_scope': 'operator 仅处理告警，不参与配置变更',
            'maintenance_scope': 'maintenance 负责摄像头/视频流维护，并可处置告警',
        }
    })
