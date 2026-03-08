from flask import Blueprint

def register_blueprints(app):
    """注册所有蓝图"""
    from .auth import auth_bp
    from .cinema import cinema_bp
    from .camera import camera_bp
    from .alarm import alarm_bp
    from .stream import stream_bp
    from .dashboard import dashboard_bp
    from .detect import detect_bp
    from .role import role_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(cinema_bp, url_prefix='/api/cinemas')
    app.register_blueprint(camera_bp, url_prefix='/api/cameras')
    app.register_blueprint(alarm_bp, url_prefix='/api/alarms')
    app.register_blueprint(stream_bp, url_prefix='/api/streams')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(detect_bp, url_prefix='/api')
    app.register_blueprint(role_bp, url_prefix='/api/roles')
