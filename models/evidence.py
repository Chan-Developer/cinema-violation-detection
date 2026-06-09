from datetime import datetime

from . import db


class MobileEvidence(db.Model):
    """手机端现场留证记录"""
    __tablename__ = 'mobile_evidences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    cinema_id = db.Column(db.Integer, db.ForeignKey('cinemas.id'), nullable=True, index=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=True, index=True)
    image_url = db.Column(db.String(500), nullable=False)
    note = db.Column(db.Text)
    location_text = db.Column(db.String(200))
    status = db.Column(db.Integer, default=0)  # 0: 已留证, 1: 已关联告警, 2: 已归档
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)

    user = db.relationship('User')
    cinema = db.relationship('Cinema')
    camera = db.relationship('Camera')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.real_name if self.user else None,
            'cinema_id': self.cinema_id,
            'cinema_name': self.cinema.name if self.cinema else None,
            'camera_id': self.camera_id,
            'camera_name': self.camera.name if self.camera else None,
            'image_url': self.image_url,
            'note': self.note,
            'location_text': self.location_text,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }
