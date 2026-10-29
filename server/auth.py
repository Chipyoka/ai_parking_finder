"""
server/auth.py

Minimal session-based auth for the admin dashboard. No JWT/OAuth - Flask's
built-in signed session cookie plus werkzeug's password hashing is enough
for this scope (single-team internal admin tool, not a public user system).

Table: users (id, username, password_hash, role DEFAULT 'user', created_at)
Only users with role='admin' can reach admin-only routes. Everything else
(the public map, site list) stays open with no login at all.
"""

import os
import sys
from functools import wraps

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from server.db import _get_connection


def get_user_by_username(username: str):
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = %s",
            (username,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return {"id": row[0], "username": row[1], "password_hash": row[2], "role": row[3]}


def create_user(username: str, password: str, role: str = "user"):
    conn = _get_connection()
    password_hash = generate_password_hash(password)
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s) RETURNING id",
            (username, password_hash, role),
        )
        new_id = cur.fetchone()[0]
    conn.commit()
    return new_id


def verify_login(username: str, password: str):
    """Returns the user dict if credentials are valid, else None."""
    user = get_user_by_username(username)
    if user is None:
        return None
    if not check_password_hash(user["password_hash"], password):
        return None
    return user


def login_user_session(user: dict):
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]


def logout_user_session():
    session.clear()


def current_user():
    if "user_id" not in session:
        return None
    return {
        "id": session["user_id"],
        "username": session["username"],
        "role": session["role"],
    }


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            return jsonify({"error": "Login required"}), 401
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            return jsonify({"error": "Login required"}), 401
        if user["role"] != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper