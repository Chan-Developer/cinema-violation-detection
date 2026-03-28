from datetime import datetime

from . import db


class VideoRecognitionResult(db.Model):
    """视频识别结果留存（按采样帧）"""
    __tablename__ = 'video_recognition_results'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(64), nullable=False, index=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'))
    cinema_id = db.Column(db.Integer, db.ForeignKey('cinemas.id'))
    frame_index = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(500))
    person_count = db.Column(db.Integer, default=0)
    violation = db.Column(db.Boolean, default=False)
    violation_codes = db.Column(db.String(200))
    llm_summary = db.Column(db.Text)
    llm_reply = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    camera = db.relationship('Camera')
    cinema = db.relationship('Cinema')

    def to_dict(self):
        codes = []
        if self.violation_codes:
            codes = [c for c in self.violation_codes.split(',') if c]

        return {
            'id': self.id,
            'task_id': self.task_id,
            'camera_id': self.camera_id,
            'cinema_id': self.cinema_id,
            'frame_index': self.frame_index,
            'image_url': self.image_url,
            'person_count': self.person_count,
            'violation': bool(self.violation),
            'violation_codes': codes,
            'llm_summary': self.llm_summary,
            'llm_reply': self.llm_reply,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }
