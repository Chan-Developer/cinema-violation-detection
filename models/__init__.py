from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# 导出所有模型
from .user import User, Role
from .cinema import Cinema, Hall, Seat
from .camera import Camera, CameraStatus
from .alarm import (
    Alarm, AlarmType, AlarmLevel, AlarmNotification, AlarmActionLog,
    ALARM_STATUS_PENDING, ALARM_STATUS_CONFIRMED, ALARM_STATUS_PROCESSING,
    ALARM_STATUS_RESOLVED, ALARM_STATUS_IGNORED, ALARM_STATUS_TEXT
)
from .video import VideoStream
from .video_recognition import VideoRecognitionResult
from .evidence import MobileEvidence

__all__ = [
    'db', 'User', 'Role', 'Cinema', 'Hall', 'Seat', 
    'Camera', 'CameraStatus', 'Alarm', 'AlarmType',
    'AlarmLevel', 'AlarmNotification', 'AlarmActionLog',
    'ALARM_STATUS_PENDING', 'ALARM_STATUS_CONFIRMED',
    'ALARM_STATUS_PROCESSING', 'ALARM_STATUS_RESOLVED',
    'ALARM_STATUS_IGNORED', 'ALARM_STATUS_TEXT',
    'VideoStream', 'VideoRecognitionResult', 'MobileEvidence'
]
