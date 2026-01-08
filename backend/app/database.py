import sqlite3
import os
import json
from datetime import datetime
from passlib.context import CryptContext

# Database configuration
DB_FILE = "users.db"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Users table with Google Auth support
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            hashed_password TEXT,
            email TEXT UNIQUE,
            google_id TEXT UNIQUE,
            avatar_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # User Preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY,
            theme TEXT DEFAULT 'light',
            analysis_mode TEXT DEFAULT 'standard',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    # Persisted Chat Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            image_preview TEXT,
            messages_json TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_password_hash(password):
    return pwd_context.hash(password[:72])

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password[:72], hashed_password)

def create_user(username=None, password=None, email=None, google_id=None, avatar=None):
    hashed_password = get_password_hash(password) if password else None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, hashed_password, email, google_id, avatar_url) 
            VALUES (?, ?, ?, ?, ?)
        """, (username, hashed_password, email, google_id, avatar))
        user_id = cursor.lastrowid
        # Initialize default preferences
        cursor.execute("INSERT INTO user_preferences (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        return None

def find_user_by_google_id(google_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, avatar_url FROM users WHERE google_id = ?", (google_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, hashed_password FROM users WHERE username = ? OR email = ?", (username, username))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[1] and verify_password(password, result[1]):
        return result[0]  # Return user_id
    return None

def save_chat_session(session_id, user_id, messages, image_preview=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    messages_json = json.dumps(messages)
    cursor.execute("""
        INSERT OR REPLACE INTO chat_sessions (id, user_id, image_preview, messages_json, last_updated)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, user_id, image_preview, messages_json, datetime.now()))
    conn.commit()
    conn.close()

def get_user_sessions(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, image_preview, messages_json, last_updated FROM chat_sessions WHERE user_id = ? ORDER BY last_updated DESC", (user_id,))
    sessions = cursor.fetchall()
    conn.close()
    return sessions

# Initialize the DB on module load
init_db()
