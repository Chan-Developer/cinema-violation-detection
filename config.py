import os
from datetime import timedelta

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cinema-detection-secret-key-2024')

    # 数据库配置 (MySQL)
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', 3306)
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'root123')
    DB_NAME = os.environ.get('DB_NAME', 'cinema_detection')

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-2024')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    ALARM_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'alarms')
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB
    
    # 允许的文件类型
    ALLOWED_IMAGE = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
    ALLOWED_VIDEO = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    
    # RTSP配置
    RTSP_TIMEOUT = 30
    FRAME_SKIP = 3  # 每隔几帧处理一次
    
    # 检测配置
    DETECTION_INTERVAL = 1.0  # 检测间隔(秒)
    CONFIDENCE_THRESHOLD = 0.5
    
    # WebSocket配置
    SOCKETIO_MESSAGE_QUEUE = None
    SOCKETIO_ASYNC_MODE = 'eventlet'
    
    @staticmethod
    def allowed_file(filename):
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return ext in Config.ALLOWED_IMAGE or ext in Config.ALLOWED_VIDEO
    
    @staticmethod
    def is_video(filename):
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return ext in Config.ALLOWED_VIDEO


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
