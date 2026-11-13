
import sqlite3
import hashlib
import secrets
from pathlib import Path

# Database stored in the main BrandShield project folder
DB_PATH = Path(__file__).resolve().parents[2] / "brandshield.db"

# Demo account details
DEMO_NAME = "BrandShield Demo"
DEMO_EMAIL = "demo@brandshield.ai"
DEMO_PASSWORD = "BSdemo@2026"


# Connect to the database
def get_connection():
    return sqlite3.connect(DB_PATH)


# Securely hash passwords
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200000
    ).hex()

    return f"{salt}${password_hash}"


# Verify entered password
def verify_password(password, stored_hash):
    try:
        salt, saved_hash = stored_hash.split("$", 1)
        return hash_password(password, salt).split("$", 1)[1] == saved_hash
    except (ValueError, AttributeError):
        return False


# Create database and users table
def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user'
            )
        """)

        # Add demo account if it doesn't already exist
        existing_user = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (DEMO_EMAIL,)
        ).fetchone()

        if existing_user is None:
            connection.execute(
                """
                INSERT INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (
                    DEMO_NAME,
                    DEMO_EMAIL,
                    hash_password(DEMO_PASSWORD),
                    "demo"
                )
            )


# Register a new user
def register_user(name, email, password):
    name = name.strip()
    email = email.strip().lower()

    if not name or not email or not password:
        return False, "Please fill in all fields."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (name, email, hash_password(password), "user")
            )

        return True, "Account created successfully."

    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."


# Verify login details
def authenticate_user(email, password):
    email = email.strip().lower()

    with get_connection() as connection:
        user = connection.execute(
            """
            SELECT id, name, email, password_hash, role
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

    if user and verify_password(password, user[3]):
        return {
            "id": user[0],
            "name": user[1],
            "email": user[2],
            "role": user[4]
        }

    return None


# Run database setup when this module is imported
initialize_database()
