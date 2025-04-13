import os
import logging
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from app import app, db
from models import User, FaceData, VehiclePlate, ParkingSpace, AttendanceRecord, PlateDetectionLog, ParkingLog
from computer_vision import process_face_recognition, process_plate_detection, analyze_parking_spaces

logger = logging.getLogger(__name__)

# Landing page
@app.route('/')
def index():
    return render_template('index.html')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Create a blank form for CSRF token
    from flask_wtf import FlaskForm
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Create a blank form for CSRF token
    from flask_wtf import FlaskForm
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        organization = request.form.get('organization')
        
        # Form validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return render_template('register.html', form=form)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', form=form)
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('register.html', form=form)
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html', form=form)
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            organization=organization
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! You can now login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during registration: {str(e)}")
            flash('An error occurred during registration.', 'danger')
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Main app routes
@app.route('/dashboard')
@login_required
def dashboard():
    # Get summary data for dashboard
    face_count = AttendanceRecord.query.filter(
        AttendanceRecord.user_id == current_user.id,
        AttendanceRecord.check_in_time >= datetime.now().replace(hour=0, minute=0, second=0)
    ).count()
    
    # For admin, show organization-wide stats
    if current_user.role == 'admin':
        org = current_user.organization
        plate_count = PlateDetectionLog.query.filter_by(organization_id=org).count()
        parking_spaces = ParkingSpace.query.filter_by(organization_id=org).count()
        occupied_spaces = ParkingSpace.query.filter_by(organization_id=org, is_occupied=True).count()
    else:
        plate_count = 0
        parking_spaces = 0
        occupied_spaces = 0
    
    return render_template(
        'dashboard.html',
        face_count=face_count,
        plate_count=plate_count,
        parking_spaces=parking_spaces,
        occupied_spaces=occupied_spaces,
        free_spaces=parking_spaces - occupied_spaces
    )

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        organization = request.form.get('organization')
        
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.organization = organization
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile: {str(e)}")
            flash('An error occurred while updating profile.', 'danger')
    
    return render_template('profile.html')

# Face recognition routes
@app.route('/face-recognition')
@login_required
def face_recognition():
    # Create a blank form for CSRF token
    from flask_wtf import FlaskForm
    form = FlaskForm()
    
    # Get user's attendance records
    attendance_records = AttendanceRecord.query.filter_by(user_id=current_user.id).order_by(AttendanceRecord.check_in_time.desc()).limit(10).all()
    
    # Check if user has registered their face
    has_face_data = FaceData.query.filter_by(user_id=current_user.id).first() is not None
    
    return render_template('face_recognition.html', 
                          attendance_records=attendance_records, 
                          has_face_data=has_face_data,
                          form=form)

@app.route('/register-face', methods=['POST'])
@login_required
def register_face():
    if 'face_image' not in request.files:
        return jsonify({"success": False, "message": "No file provided"}), 400
    
    file = request.files['face_image']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400
    
    try:
        # Process the face image to extract encodings
        face_encoding = process_face_recognition(file)
        
        if face_encoding is None:
            return jsonify({"success": False, "message": "No face detected in the image"}), 400
        
        # Delete any existing face data for this user
        FaceData.query.filter_by(user_id=current_user.id).delete()
        
        # Save new face data
        face_data = FaceData(user_id=current_user.id, face_encoding=face_encoding)
        db.session.add(face_data)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Face registered successfully"})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering face: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/face-attendance', methods=['POST'])
@login_required
def face_attendance():
    if 'face_image' not in request.files:
        return jsonify({"success": False, "message": "No file provided"}), 400
    
    file = request.files['face_image']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400
    
    try:
        # Process the face image and match against registered faces
        user_id = process_face_recognition(file, verify=True)
        
        if user_id is None:
            return jsonify({"success": False, "message": "Face not recognized or no face detected"}), 400
        
        # Check if user already has an open attendance record for today
        today = datetime.now().date()
        existing_record = AttendanceRecord.query.filter(
            AttendanceRecord.user_id == user_id,
            AttendanceRecord.check_in_time >= today,
            AttendanceRecord.check_out_time.is_(None)
        ).first()
        
        if existing_record:
            # Mark checkout time
            existing_record.check_out_time = datetime.now()
            db.session.commit()
            return jsonify({
                "success": True, 
                "message": "Check-out recorded successfully",
                "type": "check_out",
                "time": existing_record.check_out_time.strftime("%H:%M:%S")
            })
        else:
            # Create new attendance record
            new_record = AttendanceRecord(user_id=user_id)
            db.session.add(new_record)
            db.session.commit()
            return jsonify({
                "success": True, 
                "message": "Check-in recorded successfully",
                "type": "check_in",
                "time": new_record.check_in_time.strftime("%H:%M:%S")
            })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error recording attendance: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

# License plate detection routes
@app.route('/plate-detection')
@login_required
def plate_detection():
    # Create a blank form for CSRF token
    from flask_wtf import FlaskForm
    form = FlaskForm()
    
    # Get recent plate detections
    if current_user.role == 'admin':
        plate_logs = PlateDetectionLog.query.filter_by(
            organization_id=current_user.organization
        ).order_by(PlateDetectionLog.timestamp.desc()).limit(20).all()
        
        # Get registered plates
        registered_plates = VehiclePlate.query.filter_by(
            organization_id=current_user.organization
        ).all()
    else:
        plate_logs = []
        registered_plates = []
    
    return render_template('plate_detection.html', 
                          plate_logs=plate_logs, 
                          registered_plates=registered_plates,
                          form=form)

@app.route('/register-plate', methods=['POST'])
@login_required
def register_plate():
    if current_user.role != 'admin':
        return jsonify({"success": False, "message": "Unauthorized access"}), 403
    
    plate_number = request.form.get('plate_number')
    owner_name = request.form.get('owner_name')
    vehicle_make = request.form.get('vehicle_make')
    vehicle_model = request.form.get('vehicle_model')
    is_authorized = request.form.get('is_authorized') == 'true'
    
    if not plate_number:
        return jsonify({"success": False, "message": "Plate number is required"}), 400
    
    try:
        # Check if plate already exists
        existing_plate = VehiclePlate.query.filter_by(
            plate_number=plate_number,
            organization_id=current_user.organization
        ).first()
        
        if existing_plate:
            # Update existing plate
            existing_plate.owner_name = owner_name
            existing_plate.vehicle_make = vehicle_make
            existing_plate.vehicle_model = vehicle_model
            existing_plate.is_authorized = is_authorized
            db.session.commit()
            return jsonify({"success": True, "message": "Plate updated successfully"})
        else:
            # Create new plate
            new_plate = VehiclePlate(
                plate_number=plate_number,
                owner_name=owner_name,
                vehicle_make=vehicle_make,
                vehicle_model=vehicle_model,
                is_authorized=is_authorized,
                organization_id=current_user.organization
            )
            db.session.add(new_plate)
            db.session.commit()
            return jsonify({"success": True, "message": "Plate registered successfully"})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering plate: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/detect-plate', methods=['POST'])
@login_required
def detect_plate():
    if 'plate_image' not in request.files:
        return jsonify({"success": False, "message": "No file provided"}), 400
    
    file = request.files['plate_image']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400
    
    try:
        # Process the image to detect license plate
        plate_number, confidence = process_plate_detection(file)
        
        if not plate_number:
            return jsonify({"success": False, "message": "No plate detected in the image"}), 400
        
        # Check if plate is authorized
        plate_record = VehiclePlate.query.filter_by(
            plate_number=plate_number,
            organization_id=current_user.organization
        ).first()
        
        is_authorized = False
        owner_name = "Unknown"
        vehicle_info = ""
        
        if plate_record:
            is_authorized = plate_record.is_authorized
            owner_name = plate_record.owner_name or "Unknown"
            if plate_record.vehicle_make and plate_record.vehicle_model:
                vehicle_info = f"{plate_record.vehicle_make} {plate_record.vehicle_model}"
        
        # Save detection log
        filename = secure_filename(f"plate_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.seek(0)  # Reset file pointer before saving
        file.save(file_path)
        
        log_entry = PlateDetectionLog(
            plate_number=plate_number,
            confidence=confidence,
            is_authorized=is_authorized,
            image_path=f"uploads/{filename}",
            organization_id=current_user.organization
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "plate_number": plate_number,
            "confidence": confidence,
            "is_authorized": is_authorized,
            "owner_name": owner_name,
            "vehicle_info": vehicle_info
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error detecting plate: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

# Parking space analysis routes
@app.route('/parking-analysis')
@login_required
def parking_analysis():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Create a blank form for CSRF token
    from flask_wtf import FlaskForm
    form = FlaskForm()
    
    # Get parking spaces
    parking_spaces = ParkingSpace.query.filter_by(
        organization_id=current_user.organization
    ).all()
    
    # Get recent parking logs
    parking_logs = ParkingLog.query.join(ParkingSpace).filter(
        ParkingSpace.organization_id == current_user.organization
    ).order_by(ParkingLog.timestamp.desc()).limit(20).all()
    
    return render_template('parking_analysis.html', 
                          parking_spaces=parking_spaces, 
                          parking_logs=parking_logs,
                          form=form)

@app.route('/add-parking-space', methods=['POST'])
@login_required
def add_parking_space():
    if current_user.role != 'admin':
        return jsonify({"success": False, "message": "Unauthorized access"}), 403
    
    space_identifier = request.form.get('space_identifier')
    location_description = request.form.get('location_description')
    
    if not space_identifier:
        return jsonify({"success": False, "message": "Space identifier is required"}), 400
    
    try:
        # Check if space already exists
        existing_space = ParkingSpace.query.filter_by(
            space_identifier=space_identifier,
            organization_id=current_user.organization
        ).first()
        
        if existing_space:
            return jsonify({"success": False, "message": "Parking space with this identifier already exists"}), 400
        
        # Create new parking space
        new_space = ParkingSpace(
            space_identifier=space_identifier,
            location_description=location_description,
            organization_id=current_user.organization,
            is_occupied=False
        )
        db.session.add(new_space)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "Parking space added successfully",
            "space": {
                "id": new_space.id,
                "identifier": new_space.space_identifier,
                "location": new_space.location_description,
                "occupied": new_space.is_occupied
            }
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding parking space: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/analyze-parking', methods=['POST'])
@login_required
def analyze_parking():
    if current_user.role != 'admin':
        return jsonify({"success": False, "message": "Unauthorized access"}), 403
    
    if 'parking_image' not in request.files:
        return jsonify({"success": False, "message": "No file provided"}), 400
    
    file = request.files['parking_image']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400
    
    try:
        # Process the image to analyze parking spaces
        space_results = analyze_parking_spaces(file)
        
        if not space_results:
            return jsonify({"success": False, "message": "No parking spaces detected in the image"}), 400
        
        # Update parking spaces and create logs
        updated_spaces = []
        
        for space_id, is_occupied in space_results.items():
            # Get the space from database
            space = ParkingSpace.query.filter_by(
                id=space_id,
                organization_id=current_user.organization
            ).first()
            
            if space and space.is_occupied != is_occupied:
                # Status changed, update and log
                space.is_occupied = is_occupied
                
                # Create log entry
                log_entry = ParkingLog(
                    space_id=space.id,
                    is_occupied=is_occupied,
                    vehicle_plate=None  # We don't know the plate from image analysis alone
                )
                db.session.add(log_entry)
                
                updated_spaces.append({
                    "id": space.id,
                    "identifier": space.space_identifier,
                    "occupied": is_occupied
                })
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Analysis complete. {len(updated_spaces)} spaces updated.",
            "updated_spaces": updated_spaces
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error analyzing parking: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

# Reports
@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/api/attendance-data')
@login_required
def attendance_data():
    # Get attendance data for the past 7 days
    from sqlalchemy import text
    from datetime import datetime, timedelta
    
    # Get date from 7 days ago
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    if current_user.role == 'admin':
        # Admin gets data for all users in organization
        attendance_data = db.session.execute(
            text("""
            SELECT date(check_in_time) as date, count(*) as count
            FROM attendance_record
            JOIN user ON attendance_record.user_id = user.id
            WHERE user.organization = :org
            AND check_in_time >= :seven_days_ago
            GROUP BY date(check_in_time)
            ORDER BY date(check_in_time)
            """), 
            {"org": current_user.organization, "seven_days_ago": seven_days_ago}
        ).fetchall()
    else:
        # Regular user gets only their own data
        attendance_data = db.session.execute(
            text("""
            SELECT date(check_in_time) as date, count(*) as count
            FROM attendance_record
            WHERE user_id = :user_id
            AND check_in_time >= :seven_days_ago
            GROUP BY date(check_in_time)
            ORDER BY date(check_in_time)
            """), 
            {"user_id": current_user.id, "seven_days_ago": seven_days_ago}
        ).fetchall()
    
    # Format data for chart.js
    labels = [row[0] for row in attendance_data]
    values = [row[1] for row in attendance_data]
    
    return jsonify({
        "labels": labels,
        "data": values
    })

@app.route('/api/plate-data')
@login_required
def plate_data():
    if current_user.role != 'admin':
        return jsonify({"success": False, "message": "Unauthorized access"}), 403
    
    # Get license plate data for the past 7 days
    from sqlalchemy import text
    from datetime import datetime, timedelta
    
    # Get date from 7 days ago
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    plate_data = db.session.execute(
        text("""
        SELECT date(timestamp) as date, count(*) as count
        FROM plate_detection_log
        WHERE organization_id = :org
        AND timestamp >= :seven_days_ago
        GROUP BY date(timestamp)
        ORDER BY date(timestamp)
        """), 
        {"org": current_user.organization, "seven_days_ago": seven_days_ago}
    ).fetchall()
    
    # Format data for chart.js
    labels = [row[0] for row in plate_data]
    values = [row[1] for row in plate_data]
    
    return jsonify({
        "labels": labels,
        "data": values
    })

@app.route('/api/parking-data')
@login_required
def parking_data():
    if current_user.role != 'admin':
        return jsonify({"success": False, "message": "Unauthorized access"}), 403
    
    # Get current parking space statistics
    total_spaces = ParkingSpace.query.filter_by(organization_id=current_user.organization).count()
    occupied_spaces = ParkingSpace.query.filter_by(organization_id=current_user.organization, is_occupied=True).count()
    free_spaces = total_spaces - occupied_spaces
    
    return jsonify({
        "total": total_spaces,
        "occupied": occupied_spaces,
        "free": free_spaces
    })

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message="Internal server error"), 500

# Context processor to add current_year to all templates
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}
