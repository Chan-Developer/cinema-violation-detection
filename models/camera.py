from . import db
from datetime import datetime

class CameraStatus(db.Model):
    """摄像头状态记录"""
    __tablename__ = 'camera_status'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    status = db.Column(db.Integer, default=1)  # 1: 在线, 0: 离线
    cpu_usage = db.Column(db.Float)  # CPU使用率
    memory_usage = db.Column(db.Float)  # 内存使用率
    network_delay = db.Column(db.Float)  # 网络延迟(ms)
    bitrate = db.Column(db.Integer)  # 码率(kbps)
    fps = db.Column(db.Float)  # 帧率
    record_time = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    camera = db.relationship('Camera', back_populates='status_records')
    
    def to_dict(self):
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'status': self.status,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'network_delay': self.network_delay,
            'bitrate': self.bitrate,
            'fps': self.fps,
            'record_time': self.record_time.strftime('%Y-%m-%d %H:%M:%S')
        }


class Camera(db.Model):
    """摄像头表"""
    __tablename__ = 'cameras'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cinema_id = db.Column(db.Integer, db.ForeignKey('cinemas.id'), nullable=False)
    hall_id = db.Column(db.Integer, db.ForeignKey('halls.id'), nullable=True)
    
    # RTSP配置
    rtsp_url = db.Column(db.String(500))
    username = db.Column(db.String(50))
    password = db.Column(db.String(100))
    
    # 位置信息
    position = db.Column(db.String(50))  # 入口, 出口, 左侧, 右侧, 中央, 座位区
    angle = db.Column(db.Float)  # 角度
    mount_height = db.Column(db.Float)  # 安装高度
    
    # 功能配置
    detection_enabled = db.Column(db.Integer, default=1)  # 1: 启用检测, 0: 禁用
    detection_types = db.Column(db.String(200))  # 检测类型, 逗号分隔: photo, smoke, crowd, walk
    
    # 状态
    status = db.Column(db.Integer, default=0)  # 0: 离线, 1: 在线, 2: 维护中
    stream_status = db.Column(db.Integer, default=0)  # 0: 未启动, 1: 运行中
    
    # 其他
    manufacturer = db.Column(db.String(50))  # 厂商
    model = db.Column(db.String(50))  # 型号
    ip_address = db.Column(db.String(50))
    port = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    cinema = db.relationship('Cinema', back_populates='cameras')
    hall = db.relationship('Hall', back_populates='cameras')
    status_records = db.relationship('CameraStatus', back_populates='camera', lazy='dynamic', cascade='all, delete-orphan')
    alarms = db.relationship('Alarm', back_populates='camera', lazy='dynamic')
    
    def to_dict(self, include_status=False):
        data = {
            'id': self.id,
            'name': self.name,
            'cinema_id': self.cinema_id,
            'cinema_name': self.cinema.name if self.cinema else None,
            'hall_id': self.hall_id,
            'hall_name': self.hall.name if self.hall else None,
            'rtsp_url': self.rtsp_url,
            'position': self.position,
            'angle': self.angle,
            'mount_height': self.mount_height,
            'detection_enabled': self.detection_enabled,
            'detection_types': self.detection_types.split(',') if self.detection_types else [],
            'status': self.status,
            'stream_status': self.stream_status,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'ip_address': self.ip_address,
            'port': self.port,
            'alarm_count': self.alarms.count() if self.alarms else 0,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        if include_status:
            latest_status = self.status_records.order_by(CameraStatus.record_time.desc()).first()
            data['latest_status'] = latest_status.to_dict() if latest_status else None
        return data
