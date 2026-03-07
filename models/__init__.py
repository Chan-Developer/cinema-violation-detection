from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# 导出所有模型
from .user import User, Role
from .cinema import Cinema, Hall, Seat
from .camera import Camera, CameraStatus
from .alarm import Alarm, AlarmType, AlarmLevel, AlarmNotification
from .video import VideoStream

__all__ = [
    'db', 'User', 'Role', 'Cinema', 'Hall', 'Seat', 
    'Camera', 'CameraStatus', 'Alarm', 'AlarmType', 
    'AlarmLevel', 'AlarmNotification', 'VideoStream'
]
