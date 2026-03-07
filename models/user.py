from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Role(db.Model):
    """角色表"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)  # admin, manager, operator, maintenance
    description = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    users = db.relationship('User', back_populates='role', lazy='dynamic')
    
    @staticmethod
    def init_roles():
        """初始化角色"""
        roles = [
            {'name': 'admin', 'description': '系统管理员 - 全部权限'},
            {'name': 'manager', 'description': '影院经理 - 管理所属影院'},
            {'name': 'operator', 'description': '监控员 - 接收报警'},
            {'name': 'maintenance', 'description': '运维工程师 - 系统维护'}
        ]
        for role_data in roles:
            role = Role.query.filter_by(name=role_data['name']).first()
            if not role:
                role = Role(**role_data)
                db.session.add(role)
        db.session.commit()


class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    cinema_id = db.Column(db.Integer, db.ForeignKey('cinemas.id'), nullable=True)  # 影院经理所属影院
    status = db.Column(db.Integer, default=1)  # 1: 启用, 0: 禁用
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    role = db.relationship('Role', back_populates='users')
    cinema = db.relationship('Cinema', back_populates='managers')
    alarm_notifications = db.relationship('AlarmNotification', back_populates='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role.name if self.role else None,
            'role_id': self.role_id,
            'cinema_id': self.cinema_id,
            'cinema_name': self.cinema.name if self.cinema else None,
            'status': self.status,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
