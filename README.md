
---

# Kairos

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.1.0-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**SecuritySentinel** is a web-based security monitoring application built with Flask, designed to manage user authentication, face recognition, vehicle plate detection, parking space monitoring, and attendance tracking. It leverages PostgreSQL for data storage, OpenCV and `face_recognition` for computer vision tasks, and a responsive frontend for user interaction.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **User Authentication**: Secure registration and login with role-based access (admin/user) using Flask-Login and Flask-WTF.
- **Face Recognition**: Upload and process images for face detection and recognition using `face_recognition` and OpenCV.
- **Vehicle Plate Detection**: Detect and log vehicle license plates from uploaded images.
- **Parking Space Management**: Track parking space occupancy and generate logs.
- **Attendance Tracking**: Record user attendance based on face recognition.
- **Responsive UI**: Bootstrap-based templates for a user-friendly interface.
- **PostgreSQL Integration**: Store users, face data, vehicle plates, parking logs, and attendance records.
- **Logging**: Comprehensive logging for debugging and monitoring.

---

## Tech Stack

- **Backend**: Flask 3.1.0, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- **Database**: PostgreSQL
- **Computer Vision**: OpenCV, `face_recognition`, NumPy
- **Frontend**: HTML, Bootstrap, CSS, JavaScript
- **Dependencies**: Managed via `pyproject.toml`
- **Environment**: Python 3.11+, Gunicorn (for production)

---

## Prerequisites

- **Python**: Version 3.11 or higher
- **PostgreSQL**: Version 15 or higher
- **Git**: For cloning the repository
- **pip**: For installing dependencies
- Optional: Virtual environment tool (e.g., `venv`)

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/nirmaleeswar30/Kairos.git
   cd Kairos
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -e .
   ```

4. **Install PostgreSQL**:
   - Download and install from [postgresql.org](https://www.postgresql.org/download/).
   - Start the PostgreSQL service:
     ```bash
     # Linux
     sudo service postgresql start
     # macOS
     brew services start postgresql
     ```

5. **Create the Database**:
   Log in to PostgreSQL:
   ```bash
   psql -U postgres
   ```
   Create the database:
   ```sql
   CREATE DATABASE securitysystem;
   \q
   ```

---

## Configuration

1. **Database Connection**:
   The app uses a PostgreSQL URI defined in `app.py`. Set the `DATABASE_URL` environment variable:
   ```bash
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/securitysystem"
   ```
   On Windows:
   ```cmd
   set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/securitysystem
   ```

   Alternatively, update `app.py` directly:
   ```python
   app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://your_user:your_password@localhost:5432/securitysystem"
   ```

2. **Upload Folder**:
   Ensure the `static/uploads/` directory exists for storing images. It’s included in the repository but can be created:
   ```bash
   mkdir -p static/uploads
   touch static/uploads/.gitkeep
   ```

3. **Logging**:
   Logs are written to the console by default. Modify `app.py` to write to a file if needed.

---

## Running the Application

1. **Initialize the Database**:
   Run the app to create tables:
   ```bash
   python main.py
   ```
   Or use a Python shell:
   ```bash
   python
   >>> from app import app, db
   >>> with app.app_context():
   ...     db.create_all()
   ```

2. **Start the Development Server**:
   ```bash
   python main.py
   ```
   The app runs at `http://localhost:5000` in debug mode.

3. **Production (Optional)**:
   Use Gunicorn for production:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 main:app
   ```

---

## Usage

- **Access the App**: Open `http://localhost:5000` in a browser.
- **Register/Login**: Use `/register` to create a user or `/login` to sign in.
- **Admin Features**:
  - Add parking spaces via `/add-parking-space`.
  - View logs at `/logs`.
- **User Features**:
  - Upload images for face recognition or plate detection via `/upload`.
  - Check attendance records at `/attendance`.
- **API Endpoints**:
  - Check `routes.py` for available routes (e.g., `/api/users`, `/api/plates`).

---

## Project Structure

```
Kairos/
├── .gitignore           # Git ignore file
├── .replit             # Replit configuration
├── replit.nix          # Replit environment setup
├── pyproject.toml      # Dependencies and build settings
├── app.py              # Flask app configuration
├── main.py             # Entry point for running the app
├── models.py           # SQLAlchemy database models
├── routes.py           # Flask routes and logic
├── utils.py            # Utility functions (e.g., image processing)
├── computer_vision.py  # Face recognition and plate detection logic
├── static/             # CSS, JS, and uploaded images
│   ├── css/
│   ├── js/
│   └── uploads/
├── templates/          # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   └── ...
└── README.md           # This file
```

---

## Contributing

We welcome contributions! To get started:

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature
   ```
3. Commit changes:
   ```bash
   git commit -m "Add your feature"
   ```
4. Push to your fork:
   ```bash
   git push origin feature/your-feature
   ```
5. Open a pull request.

Please include tests and update documentation as needed.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

### Notes for Customization
- **Repository URL**: Replace `https://github.com/nirmaleeswar30/Kairos.git` with your actual repository URL.
- **License**: The MIT License is assumed; update to your preferred license (e.g., GPL, Apache) and include a `LICENSE` file.
- **Badges**: Shields.io badges are included for Python, Flask, and PostgreSQL. Add more (e.g., CI status) if you set up workflows.
- **Screenshots**: Consider adding screenshots of the UI (e.g., login page, dashboard) under a "Screenshots" section.
- **Production Deployment**: The README mentions Gunicorn but not a full production setup (e.g., Nginx, cloud hosting). Add a "Deployment" section if needed.
- **Replit**: The `.replit` and `replit.nix` files suggest Replit compatibility. If targeting Replit users, add a "Running on Replit" section:
  ```markdown
  ### Running on Replit
  1. Import the repository into Replit.
  2. Set `DATABASE_URL` in Replit's Secrets.
  3. Click "Run" to start the app.
  ```
