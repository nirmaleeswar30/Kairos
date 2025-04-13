// Camera.js - Handles camera functionality for face recognition and plate detection

let videoStream;
let videoElement;
let canvasElement;
let captureButton;
let processingMessage;
let resultElement;
let csrfToken;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize camera elements
    videoElement = document.getElementById('cameraFeed');
    canvasElement = document.getElementById('captureCanvas');
    captureButton = document.getElementById('captureButton');
    processingMessage = document.getElementById('processingMessage');
    resultElement = document.getElementById('resultContainer');
    
    // Get CSRF token from the hidden form
    const csrfForm = document.getElementById('csrf-form');
    if (csrfForm) {
        const csrfInput = csrfForm.querySelector('input[name="csrf_token"]');
        if (csrfInput) {
            csrfToken = csrfInput.value;
        }
    }
    
    // Set up event listeners
    setupCameraEventListeners();
    
    // Start camera if element exists
    if (videoElement) {
        startCamera();
    }
});

/**
 * Set up event listeners for camera functionality
 */
function setupCameraEventListeners() {
    if (captureButton) {
        captureButton.addEventListener('click', captureImage);
    }
    
    // Face registration button
    const registerFaceButton = document.getElementById('registerFaceButton');
    if (registerFaceButton) {
        registerFaceButton.addEventListener('click', registerFace);
    }
    
    // Face attendance button
    const faceAttendanceButton = document.getElementById('faceAttendanceButton');
    if (faceAttendanceButton) {
        faceAttendanceButton.addEventListener('click', recordAttendance);
    }
    
    // Plate detection button
    const detectPlateButton = document.getElementById('detectPlateButton');
    if (detectPlateButton) {
        detectPlateButton.addEventListener('click', detectPlate);
    }
    
    // Parking analysis button
    const analyzeParkingButton = document.getElementById('analyzeParkingButton');
    if (analyzeParkingButton) {
        analyzeParkingButton.addEventListener('click', analyzeParking);
    }
}

/**
 * Start the camera feed
 */
function startCamera() {
    // Check if getUserMedia is supported
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Request camera access
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                videoStream = stream;
                videoElement.srcObject = stream;
                videoElement.play();
                
                if (captureButton) {
                    captureButton.disabled = false;
                }
            })
            .catch(function(error) {
                console.error('Error accessing camera:', error);
                showError('Could not access the camera. Please make sure your camera is connected and you have granted permission.');
            });
    } else {
        showError('Your browser does not support camera access.');
    }
}

/**
 * Stop the camera feed
 */
function stopCamera() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
        
        if (videoElement) {
            videoElement.srcObject = null;
        }
    }
}

/**
 * Capture an image from the camera feed
 */
function captureImage() {
    if (!videoStream) {
        showError('Camera is not active. Please restart the camera.');
        return;
    }
    
    // Set canvas dimensions to match video
    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;
    
    // Draw current video frame to canvas
    const context = canvasElement.getContext('2d');
    context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
    
    // Show the captured image
    canvasElement.style.display = 'block';
    
    return canvasElement.toDataURL('image/jpeg');
}

/**
 * Convert a data URL to a Blob object
 */
function dataURLtoBlob(dataURL) {
    // Convert base64 to raw binary data held in a string
    const byteString = atob(dataURL.split(',')[1]);
    
    // Separate out the mime component
    const mimeString = dataURL.split(',')[0].split(':')[1].split(';')[0];
    
    // Write the bytes of the string to an ArrayBuffer
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    
    // Create a Blob with the ArrayBuffer
    return new Blob([ab], { type: mimeString });
}

/**
 * Register a face using the captured image
 */
function registerFace() {
    const imageData = captureImage();
    
    if (!imageData) {
        showError('Failed to capture image. Please try again.');
        return;
    }
    
    // Show processing message
    if (processingMessage) {
        processingMessage.textContent = 'Processing face...';
        processingMessage.style.display = 'block';
    }
    
    // Create form data with the image
    const formData = new FormData();
    formData.append('face_image', dataURLtoBlob(imageData), 'face.jpg');
    
    // Add CSRF token
    if (csrfToken) {
        formData.append('csrf_token', csrfToken);
    }
    
    // Send the image to the server
    fetch('/register-face', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (processingMessage) {
            processingMessage.style.display = 'none';
        }
        
        if (data.success) {
            showSuccess(data.message);
        } else {
            showError(data.message);
        }
    })
    .catch(error => {
        console.error('Error registering face:', error);
        if (processingMessage) {
            processingMessage.style.display = 'none';
        }
        showError('An error occurred while registering the face. Please try again.');
    });
}

/**
 * Record attendance using face recognition
 */
function recordAttendance() {
    const imageData = captureImage();
    
    if (!imageData) {
        showError('Failed to capture image. Please try again.');
        return;
    }
    
    // Show processing message
    if (processingMessage) {
        processingMessage.textContent = 'Processing face...';
        processingMessage.style.display = 'block';
    }
    
    // Create form data with the image
    const formData = new FormData();
    formData.append('face_image', dataURLtoBlob(imageData), 'face.jpg');
    
    // Add CSRF token
    if (csrfToken) {
        formData.append('csrf_token', csrfToken);
    }
    
    // Send the image to the server
    fetch('/face-attendance', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (processingMessage) {
            processingMessage.style.display = 'none';
        }
        
        if (data.success) {
            const checkType = data.type === 'check_in' ? 'Check-in' : 'Check-out';
            showSuccess(`${checkType} recorded at ${data.time}`);
            
            // Refresh attendance records if the container exists
            const recordsContainer = document.getElementById('attendanceRecords');
            if (recordsContainer) {
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            }
        } else {
            showError(data.message);
        }
    })
    .catch(error => {
        console.error('Error recording attendance:', error);
        if (processingMessage) {
            processingMessage.style.display = 'none';
        }
        showError('An error occurred while recording attendance. Please try again.');
    });
}

/**
 * Detect license plate in the captured image
 */
function detectPlate() {
    const imageData = captureImage();
    
    if (!imageData) {
        showError('Failed to capture image. Please try again.');
        return;
    }
    
    // Show processing message
    if (processingMessage) {
        processingMessage.textContent = 'Detecting license plate...';
        processingMessage.style.display = 'block';
    }
    
    // Create form data with the image
    const formData = new FormData();
    formData.append('plate_image', dataURLtoBlob(imageData), 'plate.jpg');
    
    // Add CSRF token
    if (csrfToken) {
        formData.append('csrf_token', csrfToken);
    }
    
    // Send the image to the server
    fetch('/detect-plate', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (processingMessage) {
            processingMessage.style.display = 'none';
        }
        
        if (data.success) {
            // Show plate detection result
            if (resultElement) {
                const authorizationStatus = data.is_authorized ? 
                    '<span class="badge bg-success">Authorized</span>' : 
                    '<span class="badge bg-danger">Unauthorized</span>';
                
                resultElement.innerHTML = `
                    <div class="alert alert-success">
                        <h4 class="alert-heading">Plate Detected!</h4>
                        <p><strong>Plate Number:</strong> ${data.plate_number}</p>
                        <p><strong>Confidence:</strong> ${(data.confidence * 100).toFixed(2)}%</p>
                        <p><strong>Status:</strong> ${authorizationStatus}</p>
                        <p><strong>Owner:</strong> ${data.owner_name}</p>
                        <p><strong>Vehicle:</strong> ${data.vehicle_info || 'Unknown'}</p>
                    </div>
                `;
                resultElement.style.display = 'block';
            }
        } else {
            showError(data.message);
        }
    })
    .catch(error => {
        console.error('Error detecting plate:', error);
        if (processingMessage) {
            processingMessage.style.display = 'none';
        }
        showError('An error occurred while detecting the license plate. Please try again.');
    });
}

/**
 * Analyze parking spaces in the captured image
 */
function analyzeParking() {
    const imageData = captureImage();
    
    if (!imageData) {
        showError('Failed to capture image. Please try again.');
        return;
    }
    
    // Show processing message
    if (processingMessage) {
        processingMessage.textContent = 'Analyzing parking spaces...';
        processingMessage.style.display = 'block';
    }
    
    // Create form data with the image
    const formData = new FormData();
    formData.append('parking_image', dataURLtoBlob(imageData), 'parking.jpg');
    
    // Add CSRF token
    if (csrfToken) {
        formData.append('csrf_token', csrfToken);
    }
    
    // Send the image to the server
    fetch('/analyze-parking', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (processingMessage) {
            processingMessage.style.display = 'none';
        }
        
        if (data.success) {
            showSuccess(data.message);
            
            // Update parking space status if any spaces were updated
            if (data.updated_spaces && data.updated_spaces.length > 0) {
                updateParkingSpaces(data.updated_spaces);
            }
        } else {
            showError(data.message);
        }
    })
    .catch(error => {
        console.error('Error analyzing parking:', error);
        if (processingMessage) {
            processingMessage.style.display = 'none';
        }
        showError('An error occurred while analyzing parking spaces. Please try again.');
    });
}

/**
 * Update parking space status in the UI
 */
function updateParkingSpaces(updatedSpaces) {
    updatedSpaces.forEach(space => {
        const spaceElement = document.getElementById(`space-${space.id}`);
        if (spaceElement) {
            // Update the status badge
            const statusBadge = spaceElement.querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.className = 'status-badge badge ' + 
                    (space.occupied ? 'bg-danger' : 'bg-success');
                statusBadge.textContent = space.occupied ? 'Occupied' : 'Free';
            }
        }
    });
    
    // Refresh the page after a short delay to show updated data
    setTimeout(() => {
        window.location.reload();
    }, 2000);
}

/**
 * Show a success message
 */
function showSuccess(message) {
    if (resultElement) {
        resultElement.innerHTML = `<div class="alert alert-success">${message}</div>`;
        resultElement.style.display = 'block';
    }
}

/**
 * Show an error message
 */
function showError(message) {
    if (resultElement) {
        resultElement.innerHTML = `<div class="alert alert-danger">${message}</div>`;
        resultElement.style.display = 'block';
    }
}
