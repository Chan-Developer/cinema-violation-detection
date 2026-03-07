from . import db
from datetime import datetime

class Cinema(db.Model):
    """影院表"""
    __tablename__ = 'cinemas'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    city = db.Column(db.String(50))
    district = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    contact = db.Column(db.String(50))
    status = db.Column(db.Integer, default=1)  # 1: 营业, 0: 停业
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    halls = db.relationship('Hall', back_populates='cinema', cascade='all, delete-orphan')
    managers = db.relationship('User', back_populates='cinema', lazy='dynamic')
    cameras = db.relationship('Camera', back_populates='cinema', lazy='dynamic')
    
    def to_dict(self, include_halls=False):
        data = {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'district': self.district,
            'phone': self.phone,
            'contact': self.contact,
            'status': self.status,
            'hall_count': len(self.halls) if self.halls else 0,
            'camera_count': self.cameras.count() if self.cameras else 0,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        if include_halls:
            data['halls'] = [hall.to_dict() for hall in self.halls]
        return data


class Hall(db.Model):
    """影厅表"""
    __tablename__ = 'halls'
    
    id = db.Column(db.Integer, primary_key=True)
    cinema_id = db.Column(db.Integer, db.ForeignKey('cinemas.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # 1号厅, 2号厅, VIP厅
    hall_type = db.Column(db.String(20))  # 普通, IMAX, VIP, 4DX
    rows = db.Column(db.Integer, default=10)
    cols = db.Column(db.Integer, default=15)
    total_seats = db.Column(db.Integer, default=150)
    status = db.Column(db.Integer, default=1)  # 1: 正常, 0: 维护
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    cinema = db.relationship('Cinema', back_populates='halls')
    cameras = db.relationship('Camera', back_populates='hall', lazy='dynamic')
    seats = db.relationship('Seat', back_populates='hall', cascade='all, delete-orphan')
    
    def to_dict(self, include_seats=False):
        data = {
            'id': self.id,
            'cinema_id': self.cinema_id,
            'cinema_name': self.cinema.name if self.cinema else None,
            'name': self.name,
            'hall_type': self.hall_type,
            'rows': self.rows,
            'cols': self.cols,
            'total_seats': self.total_seats,
            'status': self.status,
            'camera_count': self.cameras.count() if self.cameras else 0,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        if include_seats:
            data['seats'] = [seat.to_dict() for seat in self.seats]
        return data


class Seat(db.Model):
    """座位表"""
    __tablename__ = 'seats'
    
    id = db.Column(db.Integer, primary_key=True)
    hall_id = db.Column(db.Integer, db.ForeignKey('halls.id'), nullable=False)
    row = db.Column(db.String(5), nullable=False)  # A, B, C...
    number = db.Column(db.Integer, nullable=False)  # 1, 2, 3...
    seat_type = db.Column(db.String(20), default='normal')  # normal, vip, disabled
    status = db.Column(db.Integer, default=1)  # 1: 正常, 0: 损坏
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    hall = db.relationship('Hall', back_populates='seats')
    
    __table_args__ = (
        db.UniqueConstraint('hall_id', 'row', 'number', name='unique_seat'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'hall_id': self.hall_id,
            'row': self.row,
            'number': self.number,
            'seat_type': self.seat_type,
            'status': self.status,
            'seat_label': f'{self.row}{self.number}'
        }
