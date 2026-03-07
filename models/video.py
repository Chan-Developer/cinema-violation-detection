from . import db
from datetime import datetime

class VideoStream(db.Model):
    """视频流管理表"""
    __tablename__ = 'video_streams'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False, unique=True)
    
    # 流配置
    stream_url = db.Column(db.String(500))  # 实际连接的流地址
    width = db.Column(db.Integer, default=1920)
    height = db.Column(db.Integer, default=1080)
    fps = db.Column(db.Float, default=25.0)
    
    # 状态
    status = db.Column(db.Integer, default=0)  # 0: 停止, 1: 运行, 2: 错误
    error_message = db.Column(db.String(500))
    
    # _frames = db.Column统计
    total_frames = db.Column(db.Integer, default=0)
    dropped_frames = db.Column(db.Integer, default=0)
    avg_latency = db.Column(db.Float, default=0)  # 平均延迟(ms)
    
    # 控制
    auto_reconnect = db.Column(db.Integer, default=1)
    reconnect_interval = db.Column(db.Integer, default=5)  # 重连间隔(秒)
    max_reconnect = db.Column(db.Integer, default=10)  # 最大重连次数
    
    # 时间
    started_at = db.Column(db.DateTime)
    stopped_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    camera = db.relationship('Camera', backref=db.backref('stream', uselist=False))
    
    def to_dict(self):
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'camera_name': self.camera.name if self.camera else None,
            'stream_url': self.stream_url,
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'status': self.status,
            'status_text': ['停止', '运行', '错误'][self.status] if self.status < 3 else '未知',
            'error_message': self.error_message,
            'total_frames': self.total_frames,
            'dropped_frames': self.dropped_frames,
            'avg_latency': self.avg_latency,
            'auto_reconnect': self.auto_reconnect,
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'stopped_at': self.stopped_at.strftime('%Y-%m-%d %H:%M:%S') if self.stopped_at else None,
        }
