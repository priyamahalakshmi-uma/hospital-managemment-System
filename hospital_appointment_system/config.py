import os

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hospital-secret-key-college-project-2026')
    DEBUG = True

    # MySQL Database Configuration (XAMPP / WAMP / MySQL default)
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'hospital_db')

    # SQLite fallback file (used automatically if MySQL server is not running)
    SQLITE_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hospital.db')

    # Admin Portal Credentials
    ADMIN_USERNAME = os.environ.get('ADMIN_USER', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASS', 'admin123')
