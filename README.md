# Smart Attendance Management System

This repository contains the central Web Dashboard for the Smart Attendance Management System, along with references to the affiliated hardware client (`cam_`). The system automates attendance tracking using facial recognition while providing comprehensive role-based dashboards for institutional management.

## System Architecture

The project is structured into two main components:
1. **Web Dashboard (Central Server):** A Flask-based monolithic web application that manages users, timetables, attendance data, and remote hardware devices.
2. **Remote Hardware Client (`cam_` folder):** A Python-based script (often deployed on a Raspberry Pi or a local system) utilizing OpenCV and facial recognition models. It polls the server for commands and performs live facial recognition.

## Tech Stack
- **Backend:** Python, Flask, SQLite3, Werkzeug (Security)
- **Frontend:** HTML5, CSS3, Jinja2 Templates
- **Hardware Interface Client:** Python, OpenCV (`cv2`), Face Recognition Engines
- **Communication:** REST APIs & JSON-based long polling (Server & Device)

## Core Working Logic & Flow

### 1. Remote Session Control & Hardware Polling
- **Onboarding:** The hardware device initiates a connection to the server. The admin reviews and approves the device in the device management pipeline.
- **Polling:** The client continuously polls the central endpoint (`/api/device/command/<device_id>`).
- **Dispatch:** An authorized **Advisor** logs into their dashboard and clicks "Start Session". The server updates the device state to `active`.
- **Execution:** Once the client receives the active command, the camera (via `camera.py` and `face_engine.py`) activates, identifies faces, and streams raw attendance policy logs to the server. 

### 2. Attendance & Session Finalization
- **Recording:** Raw facial hits are stored in the server's `policy_logs` table, mapped against the current day and period fetched from the `timetable` schema.
- **Calculation:** The server computes an aggregated morning/afternoon state based on logic thresholds and logs historical and cumulative aggregates (`main_attendance`). 

### 3. Role-Based Capabilities
- **Admin:** System configuration, user/device management, overriding features.
- **Advisor:** Batch management, initiating/stopping physical attendance sessions, and multi-tier approval.
- **Teacher:** Subject-specific insights, managing classes they are mapped to via `teacher_subjects`.
- **Student:** Live attendance viewing, percentage monitoring, and submitting duty leave.

### 4. Duty Leave Workflow
- **Application:** Students can apply for duty leaves with evidence.
- **Multi-Level Approval:** Requests move through a state machine: `PendingAdvisor` -> `PendingFaculty` -> `PendingAdmin`. 
- **Midnight Lock:** Final admin approvals only cascade into real attendance benefits after post-midnight batch audits.

## Database Schema Highlights

The SQLite database (`database/schema_init.py`) orchestrates over 18 relational tables:
- **Core Entities:** `users`, `students`, `advisors`, `teachers`
- **Academic Setup:** `subjects`, `timetable`, `teacher_subjects`
- **Attendance Ledgers:** `main_attendance` (cumulative), `morning_attendance`, `afternoon_attendance`, `history_attendance`, `policy_logs`.
- **Hardware Integration:** `sessions`, `devices`, `device_requests`, `device_commands`.
- **Workflows:** `duty_leave_requests`.

## Setup & Deployment

1. **Prerequisites:** Python 3.9+
2. **Clone the Repo:** Ensure both the web application and `cam_` client are correctly situated.
3. **Install Dependencies:** (Run via your virtual environment)
   ```bash
   pip install flask werkzeug opencv-python ...
   ```
4. **Initialize Database:**
   ```bash
   python database/schema_init.py
   ```
   *Note: This creates all requisite tables and seeds initial subjects, timetables, and an initial `admin` account.*
5. **Run the Dashboard:**
   ```bash
   python app.py
   ```
   The dashboard runs by default on `0.0.0.0:5000`.
6. **Launch hardware client:** Start `python face_engine.py` / `camera.py` within the `cam_` client repository.
