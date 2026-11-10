-- ==========================================================
-- City Care Hospital - Hospital Appointment System Database
-- Web Technologies Project
-- Database: hospital_db
-- ==========================================================

CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;

-- ----------------------------------------------------------
-- 1. Table: doctors
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    experience_years INT NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    morning_hours VARCHAR(50) DEFAULT '9:00 AM - 1:00 PM',
    evening_hours VARCHAR(50) DEFAULT '4:00 PM - 7:00 PM',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed Doctors
INSERT INTO doctors (id, name, specialization, experience_years, morning_hours, evening_hours)
VALUES 
    (1, 'Dr. Arun Kumar', 'Cardiologist (Heart Specialist)', 12, '9:00 AM - 1:00 PM', '4:00 PM - 7:00 PM'),
    (2, 'Dr. Priya Sharma', 'Dermatologist (Skin & Hair)', 8, '9:00 AM - 1:00 PM', '4:00 PM - 7:00 PM'),
    (3, 'Dr. Rahul Raj', 'General Physician (Internal Medicine)', 10, '9:00 AM - 1:00 PM', '4:00 PM - 7:00 PM'),
    (4, 'Dr. Meera Nambiar', 'Pediatrician (Child Specialist)', 11, '9:00 AM - 1:00 PM', '4:00 PM - 7:00 PM'),
    (5, 'Dr. Sanjay Varma', 'Orthopedic Surgeon (Bone & Joint)', 15, '9:00 AM - 1:00 PM', '4:00 PM - 7:00 PM'),
    (6, 'Dr. Kavitha Balan', 'Gynecologist & Obstetrician (Women Health)', 14, '9:00 AM - 1:00 PM', '4:00 PM - 7:00 PM'),
    (7, 'Dr. Rajesh Kannan', 'Neurologist (Brain & Spine)', 9, '9:00 AM - 1:00 PM', '4:00 PM - 7:00 PM'),
    (8, 'Dr. Deepa Sundar', 'Ophthalmologist (Eye Specialist)', 7, '9:00 AM - 1:00 PM', '4:00 PM - 7:00 PM')
ON DUPLICATE KEY UPDATE name=VALUES(name), specialization=VALUES(specialization), experience_years=VALUES(experience_years);

-- ----------------------------------------------------------
-- 2. Table: appointments
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reference_id VARCHAR(30) NOT NULL UNIQUE,
    patient_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    doctor_name VARCHAR(100) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time VARCHAR(20) NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'Confirmed', -- 'Confirmed', 'Completed', 'Cancelled'
    cancellation_reason VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_reference (reference_id),
    INDEX idx_phone (phone),
    INDEX idx_doc_date (doctor_name, appointment_date)
);

-- Sample Appointment Seed
INSERT INTO appointments (reference_id, patient_name, email, phone, doctor_name, appointment_date, appointment_time, reason, status)
VALUES
    ('CCH-20261105-1001', 'Karthik Subramanian', 'karthik@example.com', '9876543211', 'Dr. Arun Kumar', '2026-11-05', '10:00 AM', 'Routine Heart Checkup', 'Confirmed'),
    ('CCH-20261105-1002', 'Ananya Ramesh', 'ananya@example.com', '9876543212', 'Dr. Priya Sharma', '2026-11-05', '11:30 AM', 'Skin rash consultation', 'Confirmed')
ON DUPLICATE KEY UPDATE reference_id=VALUES(reference_id);
