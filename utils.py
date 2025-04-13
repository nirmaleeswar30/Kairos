import os
import cv2
import logging
import numpy as np
from datetime import datetime
from werkzeug.utils import secure_filename
from app import app

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if a file has an allowed extension."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file, subfolder=''):
    """
    Save an uploaded image file to the uploads directory.
    
    Args:
        file: The file object to save
        subfolder: Optional subfolder within uploads
        
    Returns:
        The path to the saved file relative to static folder
    """
    try:
        if not file or not allowed_file(file.filename):
            logger.warning(f"Invalid file or filename: {file.filename if file else 'None'}")
            return None
        
        # Create directory if it doesn't exist
        save_dir = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(save_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = secure_filename(f"{timestamp}_{file.filename}")
        
        # Save the file
        filepath = os.path.join(save_dir, filename)
        file.save(filepath)
        
        # Return the relative path
        return os.path.join('uploads', subfolder, filename)
    
    except Exception as e:
        logger.error(f"Error saving image: {str(e)}")
        return None

def preprocess_image(image_path):
    """
    Preprocess an image for computer vision tasks.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Preprocessed image as NumPy array
    """
    try:
        # Read image
        image = cv2.imread(image_path)
        
        if image is None:
            logger.error(f"Failed to read image at {image_path}")
            return None
        
        # Resize for consistency
        image = cv2.resize(image, (640, 480))
        
        # Apply some basic preprocessing
        # - Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # - Apply Gaussian blur to reduce noise
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Return preprocessed image
        return blur
    
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return None

def format_datetime(dt):
    """Format a datetime object as a string."""
    if not dt:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_date(dt):
    """Format a datetime object as a date string."""
    if not dt:
        return "N/A"
    return dt.strftime("%Y-%m-%d")

def format_time(dt):
    """Format a datetime object as a time string."""
    if not dt:
        return "N/A"
    return dt.strftime("%H:%M:%S")

def calculate_attendance_duration(check_in, check_out):
    """
    Calculate duration between check-in and check-out times.
    
    Args:
        check_in: Check-in datetime
        check_out: Check-out datetime
        
    Returns:
        Duration as string in format "HH:MM:SS"
    """
    if not check_in or not check_out:
        return "N/A"
    
    duration = check_out - check_in
    seconds = duration.total_seconds()
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
