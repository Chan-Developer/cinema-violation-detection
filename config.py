import os
from datetime import timedelta
from urllib.parse import quote_plus
from dotenv import load_dotenv


# Always load project .env from repo root to avoid import-order/cwd issues.
ENV_PATH = os.path.join(os.path.dirname(__file__), '.env')
# Do not overwrite runtime environment variables (e.g. one-off token override).
load_dotenv(ENV_PATH, override=False)


def _db_env(name: str, default: str) -> str:
    value = os.environ.get(name, default)
    return value.strip() if isinstance(value, str) else value


def _build_db_uri() -> str:
    host = _db_env('DB_HOST', '127.0.0.1')
    port = _db_env('DB_PORT', '3306')
    user = _db_env('DB_USER', 'cinema_user')
    password = quote_plus(_db_env('DB_PASSWORD', 'cinema_pass123'))
    db_name = _db_env('DB_NAME', 'cinema_detection')
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8mb4"

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cinema-detection-secret-key-2024')

    # 数据库配置 (MySQL)
    DB_HOST = _db_env('DB_HOST', '127.0.0.1')
    DB_PORT = _db_env('DB_PORT', '3306')
    DB_USER = _db_env('DB_USER', 'cinema_user')
    DB_PASSWORD = _db_env('DB_PASSWORD', 'cinema_pass123')
    DB_NAME = _db_env('DB_NAME', 'cinema_detection')

    SQLALCHEMY_DATABASE_URI = _build_db_uri()
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


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI', 'sqlite:///:memory:')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(minutes=30)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
