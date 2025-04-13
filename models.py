from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    role = db.Column(db.String(20), default='user')  # admin, user
    organization = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    face_data = db.relationship('FaceData', backref='user', lazy=True)
    attendance_records = db.relationship('AttendanceRecord', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class FaceData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    face_encoding = db.Column(db.LargeBinary, nullable=False)  # Store face recognition encoding
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<FaceData for User {self.user_id}>'

class VehiclePlate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), nullable=False)
    owner_name = db.Column(db.String(128), nullable=True)
    vehicle_make = db.Column(db.String(64), nullable=True)
    vehicle_model = db.Column(db.String(64), nullable=True)
    is_authorized = db.Column(db.Boolean, default=False)
    organization_id = db.Column(db.String(128), nullable=False)  # To group by organization
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VehiclePlate {self.plate_number}>'

class ParkingSpace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    space_identifier = db.Column(db.String(20), nullable=False)
    location_description = db.Column(db.String(128), nullable=True)
    is_occupied = db.Column(db.Boolean, default=False)
    organization_id = db.Column(db.String(128), nullable=False)  # To group by organization
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ParkingSpace {self.space_identifier} {"Occupied" if self.is_occupied else "Free"}>'

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    check_out_time = db.Column(db.DateTime, nullable=True)
    detection_method = db.Column(db.String(20), default='face_recognition')  # face_recognition, manual, etc.
    
    def __repr__(self):
        return f'<AttendanceRecord for User {self.user_id} on {self.check_in_time.strftime("%Y-%m-%d")}>'

class PlateDetectionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.String(128), nullable=True)
    confidence = db.Column(db.Float, nullable=True)  # Confidence score of detection
    is_authorized = db.Column(db.Boolean, default=False)
    image_path = db.Column(db.String(256), nullable=True)  # Path to the captured image
    organization_id = db.Column(db.String(128), nullable=False)  # To group by organization
    
    def __repr__(self):
        return f'<PlateDetectionLog {self.plate_number} at {self.timestamp}>'

class ParkingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey('parking_space.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_occupied = db.Column(db.Boolean, nullable=False)
    vehicle_plate = db.Column(db.String(20), nullable=True)
    
    # Define relationship
    space = db.relationship('ParkingSpace', backref='logs')
    
    def __repr__(self):
        return f'<ParkingLog for Space {self.space_id} {"Occupied" if self.is_occupied else "Freed"} at {self.timestamp}>'
