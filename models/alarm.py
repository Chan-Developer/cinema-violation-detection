from . import db
from datetime import datetime

class AlarmType(db.Model):
    """报警类型表"""
    __tablename__ = 'alarm_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)  # photo, smoke, crowd, walk
    description = db.Column(db.String(200))
    icon = db.Column(db.String(50))  # 图标
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    alarms = db.relationship('Alarm', back_populates='alarm_type', lazy='dynamic')
    
    @staticmethod
    def init_types():
        """初始化报警类型"""
        types = [
            {'name': '盗摄检测', 'code': 'photo', 'description': '检测观众拍照或录制屏幕行为', 'icon': 'camera'},
            {'name': '吸烟检测', 'code': 'smoke', 'description': '检测观众在影厅内吸烟行为', 'icon': 'smoking'},
            {'name': '拥堵检测', 'code': 'crowd', 'description': '检测区域人员过度聚集', 'icon': 'users'},
            {'name': '随意走动', 'code': 'walk', 'description': '检测观众随意走动或离开座位', 'icon': 'walking'},
        ]
        for type_data in types:
            alarm_type = AlarmType.query.filter_by(code=type_data['code']).first()
            if not alarm_type:
                alarm_type = AlarmType(**type_data)
                db.session.add(alarm_type)
        db.session.commit()


class AlarmLevel(db.Model):
    """报警级别表"""
    __tablename__ = 'alarm_levels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)  # low, medium, high, critical
    priority = db.Column(db.Integer, default=0)  # 优先级, 数值越大越高
    color = db.Column(db.String(20))  # 颜色
    description = db.Column(db.String(100))
    
    @staticmethod
    def init_levels():
        """初始化报警级别"""
        levels = [
            {'name': '低', 'code': 'low', 'priority': 1, 'color': '#1890ff', 'description': '轻微异常'},
            {'name': '中', 'code': 'medium', 'priority': 2, 'color': '#faad14', 'description': '一般异常'},
            {'name': '高', 'code': 'high', 'priority': 3, 'color': '#ff4d4f', 'description': '严重异常'},
            {'name': '紧急', 'code': 'critical', 'priority': 4, 'color': '#d9363e', 'description': '紧急情况'},
        ]
        for level_data in levels:
            level = AlarmLevel.query.filter_by(code=level_data['code']).first()
            if not level:
                level = AlarmLevel(**level_data)
                db.session.add(level)
        db.session.commit()


class Alarm(db.Model):
    """报警记录表"""
    __tablename__ = 'alarms'
    
    id = db.Column(db.Integer, primary_key=True)
    alarm_type_id = db.Column(db.Integer, db.ForeignKey('alarm_types.id'), nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    level_id = db.Column(db.Integer, db.ForeignKey('alarm_levels.id'), nullable=False)
    
    # 报警详情
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))  # 位置描述
    
    # 图片/视频
    image_url = db.Column(db.String(500))
    video_url = db.Column(db.String(500))
    
    # 坐标信息
    detection_box = db.Column(db.String(100))  # 检测框坐标 x1,y1,x2,y2
    confidence = db.Column(db.Float)  # 置信度
    
    # 状态
    status = db.Column(db.Integer, default=0)  # 0: 待处理, 1: 已确认, 2: 已处理, 3: 已忽略
    handler_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 处理人
    handler_note = db.Column(db.Text)  # 处理备注
    
    # 时间
    occurred_at = db.Column(db.DateTime, default=datetime.now)  # 发生时间
    confirmed_at = db.Column(db.DateTime)  # 确认时间
    resolved_at = db.Column(db.DateTime)  # 解决时间
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    alarm_type = db.relationship('AlarmType', back_populates='alarms')
    camera = db.relationship('Camera', back_populates='alarms')
    level = db.relationship('AlarmLevel')
    handler = db.relationship('User')
    notifications = db.relationship('AlarmNotification', back_populates='alarm', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_relations=False):
        data = {
            'id': self.id,
            'alarm_type_id': self.alarm_type_id,
            'alarm_type': self.alarm_type.name if self.alarm_type else None,
            'alarm_type_code': self.alarm_type.code if self.alarm_type else None,
            'alarm_type_icon': self.alarm_type.icon if self.alarm_type else None,
            'camera_id': self.camera_id,
            'camera_name': self.camera.name if self.camera else None,
            'level_id': self.level_id,
            'level_name': self.level.name if self.level else None,
            'level_code': self.level.code if self.level else None,
            'level_color': self.level.color if self.level else None,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'image_url': self.image_url,
            'video_url': self.video_url,
            'detection_box': self.detection_box,
            'confidence': self.confidence,
            'status': self.status,
            'status_text': ['待处理', '已确认', '已处理', '已忽略'][self.status] if self.status < 4 else '未知',
            'handler_id': self.handler_id,
            'handler_name': self.handler.real_name if self.handler else None,
            'handler_note': self.handler_note,
            'occurred_at': self.occurred_at.strftime('%Y-%m-%d %H:%M:%S') if self.occurred_at else None,
            'confirmed_at': self.confirmed_at.strftime('%Y-%m-%d %H:%M:%S') if self.confirmed_at else None,
            'resolved_at': self.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if self.resolved_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        return data


class AlarmNotification(db.Model):
    """报警通知记录"""
    __tablename__ = 'alarm_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    alarm_id = db.Column(db.Integer, db.ForeignKey('alarms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    channel = db.Column(db.String(20))  # 通知渠道: email, sms, websocket, push
    status = db.Column(db.Integer, default=0)  # 0: 待发送, 1: 已发送, 2: 失败
    sent_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    alarm = db.relationship('Alarm', back_populates='notifications')
    user = db.relationship('User', back_populates='alarm_notifications')
