ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
ROLE_OPERATOR = 'operator'
ROLE_MAINTENANCE = 'maintenance'


SYSTEM_ROLE_ORDER = [
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_OPERATOR,
    ROLE_MAINTENANCE,
]


SYSTEM_ROLE_META = {
    ROLE_ADMIN: {
        'name': ROLE_ADMIN,
        'label': '管理员',
        'description': '系统管理员，拥有全局管理权限',
        'scope': 'all',
        'can_manage_users': True,
        'can_manage_roles': True,
        'can_manage_cinemas': True,
        'can_manage_cameras': True,
        'can_process_alarms': True,
    },
    ROLE_MANAGER: {
        'name': ROLE_MANAGER,
        'label': '影院经理',
        'description': '仅管理所属影院及其影厅、摄像头和告警',
        'scope': 'cinema',
        'can_manage_users': False,
        'can_manage_roles': False,
        'can_manage_cinemas': False,
        'can_manage_cameras': True,
        'can_process_alarms': True,
    },
    ROLE_OPERATOR: {
        'name': ROLE_OPERATOR,
        'label': '监控员',
        'description': '负责告警查看和处置，不负责配置管理',
        'scope': 'all',
        'can_manage_users': False,
        'can_manage_roles': False,
        'can_manage_cinemas': False,
        'can_manage_cameras': False,
        'can_process_alarms': True,
    },
    ROLE_MAINTENANCE: {
        'name': ROLE_MAINTENANCE,
        'label': '运维',
        'description': '负责摄像头与视频流运维，不参与角色和用户管理',
        'scope': 'all',
        'can_manage_users': False,
        'can_manage_roles': False,
        'can_manage_cinemas': False,
        'can_manage_cameras': True,
        'can_process_alarms': False,
    },
}


def role_name(claims):
    return (claims or {}).get('role')


def has_any_role(claims, *roles):
    return role_name(claims) in roles


def is_admin(claims):
    return has_any_role(claims, ROLE_ADMIN)


def is_manager(claims):
    return has_any_role(claims, ROLE_MANAGER)


def is_operator(claims):
    return has_any_role(claims, ROLE_OPERATOR)


def is_maintenance(claims):
    return has_any_role(claims, ROLE_MAINTENANCE)


def manager_cinema_id(claims):
    if not is_manager(claims):
        return None
    return (claims or {}).get('cinema_id')


def apply_manager_scope(claims, requested_cinema_id=None):
    """
    对影院经理强制使用 token 里的 cinema_id，避免越权访问其他影院数据。
    """
    managed_cinema_id = manager_cinema_id(claims)
    if managed_cinema_id:
        return managed_cinema_id
    return requested_cinema_id


def is_system_role(role_name_value):
    return role_name_value in SYSTEM_ROLE_META
