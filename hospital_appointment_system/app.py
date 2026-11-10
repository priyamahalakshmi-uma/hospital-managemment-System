from flask import Flask, render_template, request, jsonify, session
import random
import re
from datetime import datetime
from config import Config
from db import db

app = Flask(__name__)
app.config.from_object(Config)

# Standard doctor slots definition
MORNING_SLOTS = [
    "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM",
    "11:00 AM", "11:30 AM", "12:00 PM", "12:30 PM"
]
EVENING_SLOTS_WEEKDAY = [
    "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM",
    "06:00 PM", "06:30 PM"
]
EVENING_SLOTS_SATURDAY = [
    "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM"
]

def generate_reference_id(date_str):
    """Generates unique booking reference e.g., CCH-20261105-8492"""
    cleaned_date = date_str.replace("-", "")
    suffix = random.randint(1000, 9999)
    return f"CCH-{cleaned_date}-{suffix}"

# -------------------------------------------------------------
# Frontend Page Routes
# -------------------------------------------------------------

@app.route('/')
def home():
    """Patient Home & Booking Portal"""
    doctors = db.query("SELECT * FROM doctors ORDER BY id ASC")
    return render_template('index.html', doctors=doctors, db_mode='MySQL' if db.is_mysql else 'SQLite')

@app.route('/lookup')
def lookup_page():
    """Patient Booking Search & Cancellation Portal"""
    return render_template('lookup.html', db_mode='MySQL' if db.is_mysql else 'SQLite')

@app.route('/admin')
def admin_page():
    """Admin Dashboard Portal"""
    doctors = db.query("SELECT * FROM doctors ORDER BY id ASC")
    return render_template('admin.html', doctors=doctors, db_mode='MySQL' if db.is_mysql else 'SQLite')

# -------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------

@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    """Returns list of all doctors."""
    doctors = db.query("SELECT * FROM doctors ORDER BY id ASC")
    return jsonify({"success": True, "doctors": doctors})

@app.route('/api/available-slots', methods=['GET'])
def get_available_slots():
    """
    Returns available and booked time slots for a specific doctor on a given date.
    Prevents double-booking!
    """
    doctor = request.args.get('doctor', '').strip()
    date_str = request.args.get('date', '').strip()

    if not doctor or not date_str:
        return jsonify({"success": False, "message": "Doctor and date are required"}), 400

    try:
        app_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Sunday check (closed)
    if app_date.weekday() == 6:  # 6 is Sunday
        return jsonify({
            "success": True,
            "closed": True,
            "message": "Hospital is closed on Sundays",
            "slots": []
        })

    # Pick appropriate slot lists
    slots = list(MORNING_SLOTS)
    if app_date.weekday() == 5:  # Saturday
        slots.extend(EVENING_SLOTS_SATURDAY)
    else:
        slots.extend(EVENING_SLOTS_WEEKDAY)

    # Query already booked slots for this doctor on this date
    booked_records = db.query(
        "SELECT appointment_time FROM appointments WHERE doctor_name = %s AND appointment_date = %s AND status != 'Cancelled'",
        (doctor, date_str)
    )
    booked_times = {row['appointment_time'] for row in booked_records}

    slot_data = []
    for s in slots:
        slot_data.append({
            "time": s,
            "available": s not in booked_times
        })

    return jsonify({
        "success": True,
        "closed": False,
        "date": date_str,
        "doctor": doctor,
        "slots": slot_data
    })

@app.route('/api/appointments', methods=['POST'])
def book_appointment():
    """
    Books a new appointment.
    Performs server-side validation and checks slot collision.
    """
    data = request.get_json() or {}

    patient_name = data.get('patient_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    doctor_name = data.get('doctor_name', '').strip()
    appointment_date = data.get('appointment_date', '').strip()
    appointment_time = data.get('appointment_time', '').strip()
    reason = data.get('reason', '').strip()

    # Validation
    if not patient_name:
        return jsonify({"success": False, "message": "Patient name is required"}), 400

    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if not re.match(email_regex, email):
        return jsonify({"success": False, "message": "Valid email address is required"}), 400

    phone_regex = r'^[0-9]{10}$'
    if not re.match(phone_regex, phone):
        return jsonify({"success": False, "message": "10-digit phone number is required"}), 400

    if not doctor_name:
        return jsonify({"success": False, "message": "Please select a doctor"}), 400

    if not appointment_date:
        return jsonify({"success": False, "message": "Please select an appointment date"}), 400

    try:
        app_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
        today = datetime.now().date()
        if app_date < today:
            return jsonify({"success": False, "message": "Appointment date cannot be in the past"}), 400
        if app_date.weekday() == 6:
            return jsonify({"success": False, "message": "City Care Hospital is closed on Sundays"}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format"}), 400

    if not appointment_time:
        return jsonify({"success": False, "message": "Please select an appointment time slot"}), 400

    if not reason:
        return jsonify({"success": False, "message": "Reason for visit is required"}), 400

    # Collision Check: Ensure this doctor isn't already booked for this exact time
    conflict = db.query(
        "SELECT id FROM appointments WHERE doctor_name = %s AND appointment_date = %s AND appointment_time = %s AND status != 'Cancelled'",
        (doctor_name, appointment_date, appointment_time),
        one=True
    )
    if conflict:
        return jsonify({
            "success": False,
            "message": f"Sorry! {doctor_name} already has a booked appointment at {appointment_time} on {appointment_date}. Please pick another time slot."
        }), 409

    # Generate unique reference ID
    reference_id = generate_reference_id(appointment_date)

    # Insert into database
    try:
        last_id = db.execute(
            """
            INSERT INTO appointments (reference_id, patient_name, email, phone, doctor_name, appointment_date, appointment_time, reason, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Confirmed')
            """,
            (reference_id, patient_name, email, phone, doctor_name, appointment_date, appointment_time, reason)
        )

        created_record = db.query("SELECT * FROM appointments WHERE id = %s", (last_id,), one=True)
        # Format date for response
        if created_record and hasattr(created_record['appointment_date'], 'strftime'):
            created_record['appointment_date'] = created_record['appointment_date'].strftime('%Y-%m-%d')

        return jsonify({
            "success": True,
            "message": "Appointment booked successfully!",
            "appointment": created_record
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route('/api/appointments/search', methods=['GET'])
def search_appointments():
    """
    Search appointments by Reference ID or Phone Number.
    Used by patients to view their status.
    """
    q = request.args.get('query', '').strip()
    if not q:
        return jsonify({"success": False, "message": "Search query is required"}), 400

    results = db.query(
        """
        SELECT * FROM appointments 
        WHERE reference_id = %s OR phone = %s 
        ORDER BY appointment_date DESC, id DESC
        """,
        (q, q)
    )

    # Format dates
    for r in results:
        if hasattr(r['appointment_date'], 'strftime'):
            r['appointment_date'] = r['appointment_date'].strftime('%Y-%m-%d')

    return jsonify({
        "success": True,
        "count": len(results),
        "appointments": results
    })

@app.route('/api/appointments/<int:app_id>/status', methods=['PATCH'])
def update_appointment_status(app_id):
    """
    Update appointment status (e.g. Cancelled by patient or Completed by doctor/admin).
    """
    data = request.get_json() or {}
    new_status = data.get('status', '').strip()
    reason = data.get('reason', '').strip()

    valid_statuses = ['Confirmed', 'Completed', 'Cancelled']
    if new_status not in valid_statuses:
        return jsonify({"success": False, "message": f"Status must be one of {valid_statuses}"}), 400

    existing = db.query("SELECT * FROM appointments WHERE id = %s", (app_id,), one=True)
    if not existing:
        return jsonify({"success": False, "message": "Appointment not found"}), 404

    db.execute(
        "UPDATE appointments SET status = %s, cancellation_reason = %s WHERE id = %s",
        (new_status, reason if new_status == 'Cancelled' else None, app_id)
    )

    updated = db.query("SELECT * FROM appointments WHERE id = %s", (app_id,), one=True)
    if hasattr(updated['appointment_date'], 'strftime'):
        updated['appointment_date'] = updated['appointment_date'].strftime('%Y-%m-%d')

    return jsonify({
        "success": True,
        "message": f"Appointment status updated to {new_status}",
        "appointment": updated
    })

# -------------------------------------------------------------
# Admin API Endpoints
# -------------------------------------------------------------

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Authenticates admin user."""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return jsonify({"success": True, "message": "Login successful"})
    return jsonify({"success": False, "message": "Invalid admin username or password"}), 401

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    """Logs out admin user."""
    session.pop('admin_logged_in', None)
    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route('/api/admin/session', methods=['GET'])
def admin_session_check():
    """Check if admin is currently authenticated."""
    return jsonify({
        "logged_in": session.get('admin_logged_in', False),
        "username": Config.ADMIN_USERNAME
    })

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    """Returns analytics and key metrics for dashboard."""
    total = db.query("SELECT COUNT(*) as count FROM appointments", one=True)['count']
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_count = db.query("SELECT COUNT(*) as count FROM appointments WHERE appointment_date = %s", (today_str,), one=True)['count']
    confirmed = db.query("SELECT COUNT(*) as count FROM appointments WHERE status = 'Confirmed'", one=True)['count']
    completed = db.query("SELECT COUNT(*) as count FROM appointments WHERE status = 'Completed'", one=True)['count']
    cancelled = db.query("SELECT COUNT(*) as count FROM appointments WHERE status = 'Cancelled'", one=True)['count']
    doctors_count = db.query("SELECT COUNT(*) as count FROM doctors", one=True)['count']

    return jsonify({
        "success": True,
        "stats": {
            "total": total,
            "today": today_count,
            "confirmed": confirmed,
            "completed": completed,
            "cancelled": cancelled,
            "doctors": doctors_count
        }
    })

@app.route('/api/admin/appointments', methods=['GET'])
def admin_get_appointments():
    """
    Returns filtered and searched list of appointments for admin table.
    """
    status = request.args.get('status', '').strip()
    doctor = request.args.get('doctor', '').strip()
    date_val = request.args.get('date', '').strip()
    search = request.args.get('search', '').strip()

    query = "SELECT * FROM appointments WHERE 1=1"
    params = []

    if status and status != 'All':
        query += " AND status = %s"
        params.append(status)

    if doctor and doctor != 'All':
        query += " AND doctor_name = %s"
        params.append(doctor)

    if date_val:
        query += " AND appointment_date = %s"
        params.append(date_val)

    if search:
        query += " AND (patient_name LIKE %s OR phone LIKE %s OR reference_id LIKE %s OR email LIKE %s)"
        like_search = f"%{search}%"
        params.extend([like_search, like_search, like_search, like_search])

    query += " ORDER BY appointment_date DESC, id DESC"

    appointments = db.query(query, tuple(params))
    for a in appointments:
        if hasattr(a['appointment_date'], 'strftime'):
            a['appointment_date'] = a['appointment_date'].strftime('%Y-%m-%d')

    return jsonify({
        "success": True,
        "count": len(appointments),
        "appointments": appointments
    })

@app.route('/api/admin/appointments/<int:app_id>', methods=['DELETE'])
def admin_delete_appointment(app_id):
    """Permanently delete an appointment record."""
    if not session.get('admin_logged_in', False):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    db.execute("DELETE FROM appointments WHERE id = %s", (app_id,))
    return jsonify({"success": True, "message": "Appointment deleted successfully"})

if __name__ == '__main__':
    print("=" * 60)
    print("  City Care Hospital - Appointment Management System")
    print("  Server running on http://127.0.0.1:5000")
    print(f"  Database Mode: {'MySQL' if db.is_mysql else 'SQLite Fallback'}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
