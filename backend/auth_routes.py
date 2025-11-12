# auth_routes.py
from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
import sqlite3
from passlib.context import CryptContext
import time

router = APIRouter()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# SQLite database setup
def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at REAL
        )
    """)
    return conn


# Signup endpoint
@router.post("/auth/signup")
def signup(name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower(),))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="User already exists")

    # Hash password (limit to 72 chars)
    hashed_pw = pwd_context.hash(password[:72])

    # Insert into database
    cursor.execute(
        "INSERT INTO users (email, password, name, created_at) VALUES (?, ?, ?, ?)",
        (email.lower(), hashed_pw, name, time.time()),
    )
    conn.commit()
    conn.close()
    return {"message": "User created successfully"}


# Login endpoint
@router.post("/auth/login")
def login(email: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE email = ?", (email.lower(),))
    row = cursor.fetchone()
    conn.close()

    if not row or not pwd_context.verify(password[:72], row[0]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": "Login successful"}
