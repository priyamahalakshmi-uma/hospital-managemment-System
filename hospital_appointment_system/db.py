import os
import sqlite3
import pymysql
import pymysql.cursors
from config import Config

class DatabaseManager:
    def __init__(self):
        self.is_mysql = False
        self._test_mysql()

    def _test_mysql(self):
        """Attempts to connect to MySQL; sets is_mysql flag accordingly."""
        try:
            # First try connecting to MySQL server directly
            conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                connect_timeout=2
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
            conn.close()

            # Now connect to the database
            conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=2
            )
            self._init_mysql_tables(conn)
            conn.close()
            self.is_mysql = True
            print(f"[DATABASE] Connected to MySQL database '{Config.MYSQL_DB}' on {Config.MYSQL_HOST}:{Config.MYSQL_PORT}")
        except Exception as e:
            self.is_mysql = False
            print(f"[DATABASE] MySQL not available ({e}).")
            print(f"[DATABASE] Automatically using fallback SQLite database at: {Config.SQLITE_DB}")
            self._init_sqlite_tables()

    def _init_mysql_tables(self, conn):
        """Creates required tables in MySQL if they do not exist."""
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS doctors (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    specialization VARCHAR(100) NOT NULL,
                    experience_years INT NOT NULL,
                    morning_hours VARCHAR(50) DEFAULT '9:00 AM - 1:00 PM',
                    evening_hours VARCHAR(50) DEFAULT '4:00 PM - 7:00 PM'
                )
            """)
            cursor.execute("""
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
                    status VARCHAR(20) DEFAULT 'Confirmed',
                    cancellation_reason VARCHAR(255) NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Insert seed doctors
            doctors = [
                ('Dr. Arun Kumar', 'Cardiologist (Heart Specialist)', 12),
                ('Dr. Priya Sharma', 'Dermatologist (Skin & Hair)', 8),
                ('Dr. Rahul Raj', 'General Physician (Internal Medicine)', 10),
                ('Dr. Meera Nambiar', 'Pediatrician (Child Specialist)', 11),
                ('Dr. Sanjay Varma', 'Orthopedic Surgeon (Bone & Joint)', 15),
                ('Dr. Kavitha Balan', 'Gynecologist & Obstetrician (Women Health)', 14),
                ('Dr. Rajesh Kannan', 'Neurologist (Brain & Spine)', 9),
                ('Dr. Deepa Sundar', 'Ophthalmologist (Eye Specialist)', 7)
            ]
            for doc in doctors:
                cursor.execute("""
                    INSERT IGNORE INTO doctors (name, specialization, experience_years)
                    VALUES (%s, %s, %s)
                """, doc)
            conn.commit()

    def _init_sqlite_tables(self):
        """Creates required tables in SQLite."""
        conn = sqlite3.connect(Config.SQLITE_DB)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                specialization TEXT NOT NULL,
                experience_years INTEGER NOT NULL,
                morning_hours TEXT DEFAULT '9:00 AM - 1:00 PM',
                evening_hours TEXT DEFAULT '4:00 PM - 7:00 PM'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_id TEXT NOT NULL UNIQUE,
                patient_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                doctor_name TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'Confirmed',
                cancellation_reason TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Seed doctors
        doctors = [
            ('Dr. Arun Kumar', 'Cardiologist (Heart Specialist)', 12),
            ('Dr. Priya Sharma', 'Dermatologist (Skin & Hair)', 8),
            ('Dr. Rahul Raj', 'General Physician (Internal Medicine)', 10),
            ('Dr. Meera Nambiar', 'Pediatrician (Child Specialist)', 11),
            ('Dr. Sanjay Varma', 'Orthopedic Surgeon (Bone & Joint)', 15),
            ('Dr. Kavitha Balan', 'Gynecologist & Obstetrician (Women Health)', 14),
            ('Dr. Rajesh Kannan', 'Neurologist (Brain & Spine)', 9),
            ('Dr. Deepa Sundar', 'Ophthalmologist (Eye Specialist)', 7)
        ]
        cursor.executemany("""
            INSERT OR IGNORE INTO doctors (name, specialization, experience_years)
            VALUES (?, ?, ?)
        """, doctors)
        conn.commit()
        conn.close()

    def get_connection(self):
        if self.is_mysql:
            return pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
        else:
            conn = sqlite3.connect(Config.SQLITE_DB)
            conn.row_factory = sqlite3.Row
            return conn

    def query(self, sql, args=(), one=False):
        """Executes a SELECT query and returns list of dictionaries or single dict."""
        conn = self.get_connection()
        try:
            if self.is_mysql:
                with conn.cursor() as cursor:
                    cursor.execute(sql, args)
                    res = cursor.fetchall()
                    return (res[0] if res else None) if one else res
            else:
                # Convert %s placeholders to ? for sqlite
                sqlite_sql = sql.replace('%s', '?')
                cursor = conn.cursor()
                cursor.execute(sqlite_sql, args)
                rows = cursor.fetchall()
                dict_rows = [dict(row) for row in rows]
                return (dict_rows[0] if dict_rows else None) if one else dict_rows
        finally:
            conn.close()

    def execute(self, sql, args=()):
        """Executes an INSERT, UPDATE, or DELETE query and returns lastrowid."""
        conn = self.get_connection()
        try:
            if self.is_mysql:
                with conn.cursor() as cursor:
                    cursor.execute(sql, args)
                    last_id = cursor.lastrowid
                    conn.commit()
                    return last_id
            else:
                sqlite_sql = sql.replace('%s', '?')
                cursor = conn.cursor()
                cursor.execute(sqlite_sql, args)
                last_id = cursor.lastrowid
                conn.commit()
                return last_id
        finally:
            conn.close()

db = DatabaseManager()
