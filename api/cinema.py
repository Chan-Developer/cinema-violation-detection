from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, Cinema, Hall, Seat
from utils.roles import (
    ROLE_ADMIN,
    ROLE_MANAGER,
    has_any_role,
    is_admin,
    is_manager,
    manager_cinema_id,
)

cinema_bp = Blueprint('cinema', __name__)


def get_current_user_info():
    """获取当前用户信息"""
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    return user_id, claims


@cinema_bp.route('', methods=['GET'])
@jwt_required()
def get_cinemas():
    """获取影院列表"""
    _, claims = get_current_user_info()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword')
    city = request.args.get('city')
    status = request.args.get('status', type=int)

    query = Cinema.query

    # 影院经理只能看到自己管理的影院
    scoped_cinema_id = manager_cinema_id(claims)
    if scoped_cinema_id:
        query = query.filter(Cinema.id == scoped_cinema_id)

    if keyword:
        query = query.filter(Cinema.name.contains(keyword))
    if city:
        query = query.filter(Cinema.city == city)
    if status is not None:
        query = query.filter(Cinema.status == status)

    pagination = query.order_by(Cinema.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'success': True,
        'cinemas': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page
    })


@cinema_bp.route('/<int:cinema_id>', methods=['GET'])
@jwt_required()
def get_cinema(cinema_id):
    """获取影院详情"""
    _, claims = get_current_user_info()
    scoped_cinema_id = manager_cinema_id(claims)
    if scoped_cinema_id and scoped_cinema_id != cinema_id:
        return jsonify({'success': False, 'message': '仅可访问所属影院'}), 403

    cinema = Cinema.query.get(cinema_id)
    if not cinema:
        return jsonify({'success': False, 'message': '影院不存在'}), 404
    
    return jsonify({'success': True, 'cinema': cinema.to_dict(include_halls=True)})


@cinema_bp.route('', methods=['POST'])
@jwt_required()
def create_cinema():
    """创建影院"""
    _, claims = get_current_user_info()
    if not is_admin(claims):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    data = request.get_json(silent=True) or {}
    name = data.get('name')

    if not name:
        return jsonify({'success': False, 'message': '影院名称不能为空'}), 400

    cinema = Cinema(
        name=name,
        address=data.get('address'),
        city=data.get('city'),
        district=data.get('district'),
        phone=data.get('phone'),
        contact=data.get('contact'),
        status=1
    )

    db.session.add(cinema)
    db.session.commit()

    return jsonify({'success': True, 'message': '影院创建成功', 'cinema': cinema.to_dict()})


@cinema_bp.route('/<int:cinema_id>', methods=['PUT'])
@jwt_required()
def update_cinema(cinema_id):
    """更新影院"""
    _, claims = get_current_user_info()
    if not has_any_role(claims, ROLE_ADMIN, ROLE_MANAGER):
        return jsonify({'success': False, 'message': '权限不足'}), 403
    if is_manager(claims) and manager_cinema_id(claims) != cinema_id:
        return jsonify({'success': False, 'message': '仅可更新所属影院'}), 403

    cinema = Cinema.query.get(cinema_id)
    if not cinema:
        return jsonify({'success': False, 'message': '影院不存在'}), 404

    data = request.get_json(silent=True) or {}
    
    if 'name' in data:
        cinema.name = data['name']
    if 'address' in data:
        cinema.address = data['address']
    if 'city' in data:
        cinema.city = data['city']
    if 'district' in data:
        cinema.district = data['district']
    if 'phone' in data:
        cinema.phone = data['phone']
    if 'contact' in data:
        cinema.contact = data['contact']
    if 'status' in data:
        cinema.status = data['status']
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': '影院更新成功', 'cinema': cinema.to_dict()})


@cinema_bp.route('/<int:cinema_id>', methods=['DELETE'])
@jwt_required()
def delete_cinema(cinema_id):
    """删除影院"""
    _, claims = get_current_user_info()
    if not is_admin(claims):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    cinema = Cinema.query.get(cinema_id)
    if not cinema:
        return jsonify({'success': False, 'message': '影院不存在'}), 404

    # 检查是否有影厅关联
    hall_count = Hall.query.filter_by(cinema_id=cinema_id).count()
    if hall_count > 0:
        return jsonify({'success': False, 'message': f'该影院下有{hall_count}个影厅，无法删除'}), 400

    # 检查是否有摄像头关联
    from models import Camera
    camera_count = Camera.query.filter_by(cinema_id=cinema_id).count()
    if camera_count > 0:
        return jsonify({'success': False, 'message': f'该影院下有{camera_count}个摄像头，无法删除'}), 400

    db.session.delete(cinema)
    db.session.commit()

    return jsonify({'success': True, 'message': '影院删除成功'})


# ============== 影厅管理 ==============

@cinema_bp.route('/<int:cinema_id>/halls', methods=['GET'])
@jwt_required()
def get_halls(cinema_id):
    """获取影厅列表"""
    halls = Hall.query.filter_by(cinema_id=cinema_id).all()
    return jsonify({'success': True, 'halls': [h.to_dict() for h in halls]})


@cinema_bp.route('/<int:cinema_id>/halls', methods=['POST'])
@jwt_required()
def create_hall(cinema_id):
    """创建影厅"""
    _, claims = get_current_user_info()
    if not has_any_role(claims, ROLE_ADMIN, ROLE_MANAGER):
        return jsonify({'success': False, 'message': '权限不足'}), 403
    if is_manager(claims) and manager_cinema_id(claims) != cinema_id:
        return jsonify({'success': False, 'message': '仅可管理所属影院'}), 403

    cinema = Cinema.query.get(cinema_id)
    if not cinema:
        return jsonify({'success': False, 'message': '影院不存在'}), 404

    data = request.get_json(silent=True) or {}
    name = data.get('name')

    if not name:
        return jsonify({'success': False, 'message': '影厅名称不能为空'}), 400

    # 验证行数和列数
    rows = data.get('rows', 10)
    cols = data.get('cols', 15)

    if not isinstance(rows, int) or rows < 1 or rows > 26:
        return jsonify({'success': False, 'message': '影厅行数必须在1-26之间'}), 400

    if not isinstance(cols, int) or cols < 1 or cols > 100:
        return jsonify({'success': False, 'message': '影厅列数必须在1-100之间'}), 400

    hall = Hall(
        cinema_id=cinema_id,
        name=name,
        hall_type=data.get('hall_type'),
        rows=rows,
        cols=cols,
        total_seats=rows * cols,
        status=1
    )

    db.session.add(hall)
    db.session.commit()

    # 自动生成座位
    rows_letter = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for r in range(hall.rows):
        row_name = rows_letter[r]
        for n in range(1, hall.cols + 1):
            seat = Seat(
                hall_id=hall.id,
                row=row_name,
                number=n,
                seat_type='normal',
                status=1
            )
            db.session.add(seat)
    db.session.commit()

    return jsonify({'success': True, 'message': '影厅创建成功', 'hall': hall.to_dict()})


@cinema_bp.route('/halls/<int:hall_id>', methods=['PUT'])
@jwt_required()
def update_hall(hall_id):
    """更新影厅"""
    _, claims = get_current_user_info()
    if not has_any_role(claims, ROLE_ADMIN, ROLE_MANAGER):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    hall = Hall.query.get(hall_id)
    if not hall:
        return jsonify({'success': False, 'message': '影厅不存在'}), 404
    if is_manager(claims) and manager_cinema_id(claims) != hall.cinema_id:
        return jsonify({'success': False, 'message': '仅可管理所属影院'}), 403

    data = request.get_json(silent=True) or {}

    if 'name' in data:
        hall.name = data['name']
    if 'hall_type' in data:
        hall.hall_type = data['hall_type']
    if 'rows' in data:
        rows = data['rows']
        if not isinstance(rows, int) or rows < 1 or rows > 26:
            return jsonify({'success': False, 'message': '影厅行数必须在1-26之间'}), 400
        hall.rows = rows
    if 'cols' in data:
        cols = data['cols']
        if not isinstance(cols, int) or cols < 1 or cols > 100:
            return jsonify({'success': False, 'message': '影厅列数必须在1-100之间'}), 400
        hall.cols = cols
    if 'status' in data:
        hall.status = data['status']

    hall.total_seats = hall.rows * hall.cols
    db.session.commit()

    return jsonify({'success': True, 'message': '影厅更新成功', 'hall': hall.to_dict()})


@cinema_bp.route('/halls/<int:hall_id>', methods=['DELETE'])
@jwt_required()
def delete_hall(hall_id):
    """删除影厅"""
    _, claims = get_current_user_info()
    if not is_admin(claims):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    hall = Hall.query.get(hall_id)
    if not hall:
        return jsonify({'success': False, 'message': '影厅不存在'}), 404

    # 检查是否有摄像头关联
    from models import Camera
    camera_count = Camera.query.filter_by(hall_id=hall_id).count()
    if camera_count > 0:
        return jsonify({'success': False, 'message': f'该影厅下有{camera_count}个摄像头，无法删除'}), 400

    # 删除关联的座位
    Seat.query.filter_by(hall_id=hall_id).delete()

    db.session.delete(hall)
    db.session.commit()

    return jsonify({'success': True, 'message': '影厅删除成功'})


# ============== 座位管理 ==============

@cinema_bp.route('/halls/<int:hall_id>/seats', methods=['GET'])
@jwt_required()
def get_seats(hall_id):
    """获取座位列表"""
    seats = Seat.query.filter_by(hall_id=hall_id).all()
    return jsonify({'success': True, 'seats': [s.to_dict() for s in seats]})


@cinema_bp.route('/halls/<int:hall_id>/seats', methods=['POST'])
@jwt_required()
def create_seats(hall_id):
    """批量创建座位"""
    _, claims = get_current_user_info()
    if not has_any_role(claims, ROLE_ADMIN, ROLE_MANAGER):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    hall = Hall.query.get(hall_id)
    if not hall:
        return jsonify({'success': False, 'message': '影厅不存在'}), 404
    if is_manager(claims) and manager_cinema_id(claims) != hall.cinema_id:
        return jsonify({'success': False, 'message': '仅可管理所属影院'}), 403
    
    # 删除旧座位
    Seat.query.filter_by(hall_id=hall_id).delete()
    
    # 重新生成座位
    rows = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    created = 0
    for r in range(hall.rows):
        row_name = rows[r]
        for n in range(1, hall.cols + 1):
            seat = Seat(
                hall_id=hall_id,
                row=row_name,
                number=n,
                seat_type='normal',
                status=1
            )
            db.session.add(seat)
            created += 1
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'座位生成成功，共{created}个座位'})
