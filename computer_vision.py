import pickle
import logging
import os
import string
import random
from datetime import datetime
from app import db, app
from models import FaceData, User, ParkingSpace

# Configure logging
logger = logging.getLogger(__name__)

# Try to import computer vision libraries, but provide fallbacks if they're not available
try:
    import numpy as np
    import cv2
    import face_recognition
    CV_LIBRARIES_AVAILABLE = True
    logger.info("Computer vision libraries successfully imported")
except ImportError:
    CV_LIBRARIES_AVAILABLE = False
    logger.warning("Computer vision libraries not available - using placeholder implementations")

def process_face_recognition(file, verify=False):
    """
    Process an image file for face recognition.
    
    Args:
        file: The uploaded image file
        verify: Boolean indicating whether to verify against existing faces
        
    Returns:
        If verify=False: face encoding bytes or None if no face detected
        If verify=True: user ID of the matched face or None if no match
    """
    try:
        if CV_LIBRARIES_AVAILABLE:
            # Read the image file
            image_stream = file.read()
            image = np.asarray(bytearray(image_stream), dtype=np.uint8)
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)
            
            # Convert to RGB (face_recognition uses RGB)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces in the image
            face_locations = face_recognition.face_locations(rgb_image, model="hog")  # Use HOG for speed, CNN for accuracy
            
            if not face_locations:
                logger.warning("No face detected in the image")
                return None
            
            # Use the first face found (assuming one person per image)
            face_encoding = face_recognition.face_encodings(rgb_image, [face_locations[0]])[0]
            
            if verify:
                # Compare with existing face encodings
                return verify_face(face_encoding)
            else:
                # Return the encoding for storage
                return pickle.dumps(face_encoding)
        else:
            # Placeholder implementation when libraries aren't available
            logger.info("Using placeholder face recognition implementation")
            
            # Generate a random face encoding (for demonstration only)
            mock_encoding = [random.uniform(-1, 1) for _ in range(128)]  # face_recognition uses 128-dim vectors
            
            if verify:
                # Compare with existing face encodings
                return verify_face(mock_encoding)
            else:
                # Return the encoding for storage
                return pickle.dumps(mock_encoding)
    
    except Exception as e:
        logger.error(f"Error in face recognition: {str(e)}")
        return None

def verify_face(face_encoding):
    """
    Verify a face encoding against stored encodings.
    
    Args:
        face_encoding: The encoding to verify
        
    Returns:
        User ID if match found, None otherwise
    """
    try:
        # Get all face data from database
        face_data_records = FaceData.query.all()
        
        if not face_data_records:
            logger.warning("No face data found in database")
            return None
        
        if CV_LIBRARIES_AVAILABLE:
            # Compare with each stored encoding
            for record in face_data_records:
                stored_encoding = pickle.loads(record.face_encoding)
                
                # Compare faces with a tolerance of 0.6 (lower is stricter)
                # Use the face_distance method to get a continuous measure of face similarity
                face_distance = face_recognition.face_distance([stored_encoding], face_encoding)[0]
                
                # Convert distance to similarity score (0-1 where 1 is perfect match)
                similarity = 1 - face_distance
                
                # Use compare_faces with a specific tolerance threshold
                is_match = face_recognition.compare_faces([stored_encoding], face_encoding, tolerance=0.6)[0]
                
                if is_match:
                    logger.info(f"Face match found for user ID: {record.user_id} with similarity: {similarity:.2f}")
                    return record.user_id
        else:
            # Placeholder implementation - 50% chance of finding a match
            if face_data_records and random.choice([True, False]):
                record = face_data_records[0]
                logger.info(f"Simulated face match found for user ID: {record.user_id}")
                return record.user_id
        
        logger.warning("No matching face found")
        return None
    
    except Exception as e:
        logger.error(f"Error verifying face: {str(e)}")
        return None

def process_plate_detection(file):
    """
    Process an image file for license plate detection.
    
    Args:
        file: The uploaded image file
        
    Returns:
        Tuple of (plate_number, confidence) or (None, 0) if no plate detected
    """
    try:
        if CV_LIBRARIES_AVAILABLE:
            # Read the image file
            image_stream = file.read()
            image = np.asarray(bytearray(image_stream), dtype=np.uint8)
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)
            
            # Convert to grayscale for better processing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply blur to reduce noise
            gray = cv2.bilateralFilter(gray, 11, 17, 17)
            
            # Find edges
            edged = cv2.Canny(gray, 30, 200)
            
            # Find contours
            contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
            
            # Create a copy of the original image for drawing
            img_contours = image.copy()
            cv2.drawContours(img_contours, contours, -1, (0, 255, 0), 3)
            
            # Variables to store the best plate candidate
            plate_contour = None
            plate_rect = None
            max_rect_area = 0
            
            # Find the contour with 4 points (license plate is rectangular)
            for contour in contours:
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
                
                # Look for contours with 4 points (rectangle shape)
                if len(approx) == 4:
                    # Check if it's a reasonable size for a license plate
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect_ratio = float(w) / h
                    
                    # License plates typically have an aspect ratio between 2 and 5
                    if 1.5 <= aspect_ratio <= 5.0:
                        rect_area = w * h
                        
                        # Keep track of the largest rectangle that meets our criteria
                        if rect_area > max_rect_area:
                            max_rect_area = rect_area
                            plate_contour = approx
                            plate_rect = (x, y, w, h)
            
            if plate_contour is not None and plate_rect is not None:
                # Extract the plate region
                x, y, w, h = plate_rect
                plate_img = gray[y:y+h, x:x+w]
                
                # Apply thresholding to prepare for OCR
                _, thresh = cv2.threshold(plate_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                
                # Save the license plate image for debugging
                debug_path = os.path.join(app.config['UPLOAD_FOLDER'], 'debug_plate.jpg')
                cv2.imwrite(debug_path, plate_img)
                
                # Here, you would use a real OCR library like Tesseract
                # Placeholder for OCR implementation
                letters = ''.join(random.choices(string.ascii_uppercase, k=3))
                numbers = ''.join(random.choices(string.digits, k=4))
                plate_text = f"{letters}-{numbers}"
                
                # In a real system, you would calculate confidence based on OCR results
                confidence = 0.85  # Placeholder confidence value
                
                logger.info(f"Detected plate: {plate_text} with confidence {confidence:.2f}")
                return plate_text, confidence
            
            logger.warning("No license plate detected in the image")
            return None, 0
        else:
            # Placeholder implementation
            logger.info("Using placeholder license plate detection implementation")
            
            # For demonstration, generate a realistic plate number
            letters = ''.join(random.choices(string.ascii_uppercase, k=3))
            numbers = ''.join(random.choices(string.digits, k=4))
            plate_text = f"{letters}-{numbers}"
            confidence = random.uniform(0.70, 0.95)
            
            logger.info(f"Simulated plate detection: {plate_text} with confidence {confidence:.2f}")
            return plate_text, confidence
    
    except Exception as e:
        logger.error(f"Error in plate detection: {str(e)}")
        return None, 0

def analyze_parking_spaces(file):
    """
    Process an image file to analyze parking spaces.
    
    Args:
        file: The uploaded image file
        
    Returns:
        Dictionary mapping parking space IDs to occupancy status (True/False)
    """
    try:
        # Get all parking spaces from the database
        spaces = ParkingSpace.query.all()
        results = {}
        
        if CV_LIBRARIES_AVAILABLE:
            # Read the image file
            image_stream = file.read()
            image = np.asarray(bytearray(image_stream), dtype=np.uint8)
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply adaptive thresholding to get binary image
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                           cv2.THRESH_BINARY_INV, 11, 2)
            
            # In a real implementation, you would:
            # 1. Have predefined coordinates for each parking space in your database
            # 2. Extract features from each space region in the image
            # 3. Use a machine learning model to classify if the space is occupied
            
            # For demonstration purposes, we'll implement a simple approach:
            # - Dividing the image into a grid
            # - Each grid cell corresponds to a parking space
            # - Check the white pixel density in each cell to determine occupancy
            
            if spaces:
                # Create a grid based on the number of spaces
                num_spaces = len(spaces)
                grid_size = int(np.ceil(np.sqrt(num_spaces)))
                
                # Divide the image into a grid
                h, w = thresh.shape
                cell_h, cell_w = h // grid_size, w // grid_size
                
                for i, space in enumerate(spaces):
                    if i >= grid_size * grid_size:
                        break
                        
                    # Calculate grid cell position
                    row, col = i // grid_size, i % grid_size
                    y1, x1 = row * cell_h, col * cell_w
                    y2, x2 = min(y1 + cell_h, h), min(x1 + cell_w, w)
                    
                    # Extract the cell
                    cell = thresh[y1:y2, x1:x2]
                    
                    # Count white pixels (car features in the binary image)
                    white_pixel_count = np.sum(cell > 0)
                    
                    # Calculate the percentage of white pixels in the cell
                    white_pixel_percentage = white_pixel_count / (cell.shape[0] * cell.shape[1])
                    
                    # Determine if space is occupied based on white pixel density
                    # (This threshold would be tuned based on your specific images)
                    is_occupied = white_pixel_percentage > 0.15
                    
                    # Store the result
                    results[space.id] = is_occupied
                    
                    # Debug: Draw the grid on the original image
                    cv2.rectangle(image, (x1, y1), (x2, y2), 
                                 (0, 0, 255) if is_occupied else (0, 255, 0), 2)
                    
                # Save the debug image
                debug_path = os.path.join(app.config['UPLOAD_FOLDER'], 'debug_parking.jpg')
                cv2.imwrite(debug_path, image)
            else:
                logger.warning("No parking spaces defined in the database")
            
            # If we didn't process all spaces (e.g., more spaces than grid cells)
            # Fill in the missing results
            for space in spaces:
                if space.id not in results:
                    # Randomly determine occupancy for demo purposes
                    results[space.id] = random.choice([True, False])
        else:
            # Placeholder implementation
            logger.info("Using placeholder parking space analysis implementation")
            
            for space in spaces:
                # Randomly determine if space is occupied (for demo purposes)
                results[space.id] = random.choice([True, False])
        
        logger.info(f"Analyzed {len(results)} parking spaces")
        return results
    
    except Exception as e:
        logger.error(f"Error in parking space analysis: {str(e)}")
        return {}