# 🏥 City Care Hospital - Hospital Appointment System
> **Academic Project for Web Technologies Course**  
> **Tech Stack:** HTML5, CSS3, JavaScript (Frontend) + Python & Flask (Backend) + MySQL (Database)

---

## 📌 Project Overview
The **City Care Hospital Appointment System** is a full-stack web application designed to automate outpatient doctor consultations. It replaces manual register-based appointments with an automated digital system featuring:
- **Patient Booking Portal** with real-time slot checking (prevents double booking).
- **Printable / Downloadable Appointment Slip** with unique reference IDs (e.g., `CCH-20261105-8492`).
- **Patient Booking Lookup & Cancellation** to check status and cancel upcoming visits.
- **Hospital Administration & Receptionist Dashboard** with key performance indicators (KPIs), multi-column search, date/doctor filters, and status controls.
- **Fail-Safe Database Layer**: Works with **MySQL** (via XAMPP / WAMP / MySQL Server) and automatically falls back to **SQLite** if MySQL is not running.

---

## 🏗️ System Architecture

```
[ Client Browser (HTML5 / CSS3 / JavaScript ES6) ]
                         │
               HTTP GET / POST / PATCH / DELETE
                         ▼
        [ Flask RESTful API Backend (Python) ]
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
[ MySQL Database (XAMPP/Server) ]  [ SQLite Fallback DB ]
```

### Directory Structure
```
hospital_appointment_system/
├── app.py                  # Main Flask application & REST API routes
├── db.py                   # Unified Database Manager (MySQL + SQLite fallback)
├── config.py               # Database and authentication configurations
├── schema.sql              # MySQL DDL script with tables & seed records
├── requirements.txt        # Python package dependencies
├── hospital.db             # Local SQLite database (auto-generated)
├── static/
│   ├── css/
│   │   └── style.css       # Responsive styling, cards, modal, print styles
│   └── js/
│       └── main.js         # Client validation, dynamic slot loading, modal slip
└── templates/
    ├── index.html          # Patient Home, Doctor Roster & Booking Form
    ├── lookup.html         # Appointment search, status track & cancellation
    └── admin.html          # Admin Dashboard, KPIs, appointment management table
```

---

## 🗄️ Database Design

### 1. `doctors` Table
| Column | Type | Description |
|---|---|---|
| `id` | INT AUTO_INCREMENT (PK) | Doctor ID |
| `name` | VARCHAR(100) UNIQUE | Doctor's full name |
| `specialization` | VARCHAR(100) | Department (e.g. Cardiologist) |
| `experience_years` | INT | Years of experience |
| `morning_hours` | VARCHAR(50) | Morning consultation timings |
| `evening_hours` | VARCHAR(50) | Evening consultation timings |

### 2. `appointments` Table
| Column | Type | Description |
|---|---|---|
| `id` | INT AUTO_INCREMENT (PK) | Primary Key |
| `reference_id` | VARCHAR(30) UNIQUE | Unique token (e.g. `CCH-20261105-1001`) |
| `patient_name` | VARCHAR(120) | Patient full name |
| `email` | VARCHAR(120) | Patient email address |
| `phone` | VARCHAR(20) | 10-digit phone number |
| `doctor_name` | VARCHAR(100) | Assigned doctor |
| `appointment_date` | DATE | Date of appointment |
| `appointment_time` | VARCHAR(20) | Time slot (e.g. `10:00 AM`) |
| `reason` | TEXT | Purpose of consultation |
| `status` | VARCHAR(20) | `Confirmed`, `Completed`, `Cancelled` |
| `cancellation_reason`| VARCHAR(255) | Reason if cancelled |
| `created_at` | TIMESTAMP | Record creation timestamp |

---

## 🔌 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Patient Booking Homepage |
| `GET` | `/lookup` | Patient Booking Search & Cancellation Portal |
| `GET` | `/admin` | Hospital Administration Dashboard |
| `GET` | `/api/doctors` | Get all registered doctors |
| `GET` | `/api/available-slots?doctor=...&date=...` | Returns live slots & booked status for a doctor/date |
| `POST` | `/api/appointments` | Book appointment (checks conflicts, returns reference ID) |
| `GET` | `/api/appointments/search?query=...` | Search appointments by Reference ID or Phone number |
| `PATCH` | `/api/appointments/<id>/status` | Update status (`Confirmed`, `Completed`, `Cancelled`) |
| `GET` | `/api/admin/stats` | Analytics metrics (Total, Today's, Confirmed, Cancelled) |
| `GET` | `/api/admin/appointments` | Filter & search appointments table for admin |
| `POST` | `/api/admin/login` | Staff authentication (`admin` / `admin123`) |
| `POST` | `/api/admin/logout` | Staff logout |
| `DELETE` | `/api/admin/appointments/<id>` | Permanently delete appointment |

---

## 🚀 How to Run the Project

### Prerequisites
- Python 3.10+ installed
- *(Optional for MySQL)* XAMPP, WAMP, or standalone MySQL Server

### Step 1: Install Dependencies
Open PowerShell or Terminal inside the project folder:
```powershell
pip install -r requirements.txt
```

### Step 2: (Optional) MySQL Setup via XAMPP
1. Open **XAMPP Control Panel** and start **MySQL** (and Apache).
2. Open your browser and go to `http://localhost/phpmyadmin`.
3. Click the **Import** tab.
4. Choose the file `schema.sql` from the project directory and click **Go**.
5. *Note:* If MySQL credentials differ from `root` with empty password, update `config.py`.

*(If MySQL is not started, the application will automatically run seamlessly using the local SQLite database fallback without errors).*

### Step 3: Start the Flask Web Server
Run:
```powershell
python app.py
```

### Step 4: Access the Application
- **Patient Portal (Book Appointment):** [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **Check Booking Status & Cancel:** [http://127.0.0.1:5000/lookup](http://127.0.0.1:5000/lookup)
- **Admin Dashboard:** [http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin)  
  *Credentials:* Username: `admin` | Password: `admin123`

---

## 🎓 Viva-Voce Questions & Model Answers

### Q1: What is the difference between Client-Side and Server-Side Validation?
> **Answer:** Client-side validation runs in the browser using JavaScript before sending data across the network, providing instant user feedback (e.g., regex check for 10-digit phone number or email format). Server-side validation runs in Flask (`app.py`) to guarantee security and data integrity, protecting against bypassed frontend forms or API tampering.

### Q2: How does the system prevent double-booking (slot collision)?
> **Answer:** When a user selects a doctor and date, the client sends an AJAX `GET /api/available-slots` request. The backend checks existing non-cancelled records in MySQL/SQLite for that doctor and date, disabling already-booked slots in the UI. Furthermore, on form submission (`POST /api/appointments`), the server queries the database again; if another user claimed the slot concurrently, the server rejects it with an HTTP `409 Conflict` status code.

### Q3: What is a RESTful API?
> **Answer:** REST (Representational State Transfer) is an architectural style for network-based applications that uses standard HTTP methods:
> - `GET` to retrieve records (e.g. `/api/appointments/search`)
> - `POST` to create resources (e.g. `/api/appointments`)
> - `PATCH` to update partial resources (e.g. `/api/appointments/<id>/status`)
> - `DELETE` to remove resources (e.g. `/api/admin/appointments/<id>`)

### Q4: Why is SQL parameterized query used instead of string concatenation?
> **Answer:** Parameterized queries (using `%s` or `?`) separate SQL commands from user input data. The database engine treats the parameters strictly as literal values rather than executable SQL syntax, completely eliminating **SQL Injection (SQLi)** vulnerabilities.
