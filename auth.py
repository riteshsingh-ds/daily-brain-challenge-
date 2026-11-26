
import hashlib
import hmac
import secrets
import sqlite3
import streamlit as st

from database import get_db_connection


# Password security configuration
HASH_NAME = "sha256"
ITERATIONS = 310000
SALT_LENGTH = 32


def hash_password(password, salt=None):
    """Generate a secure PBKDF2 password hash."""

    if salt is None:
        salt = secrets.token_hex(SALT_LENGTH)

    password_hash = hashlib.pbkdf2_hmac(
        HASH_NAME,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        ITERATIONS
    ).hex()

    return password_hash, salt


def verify_password(password, stored_hash, salt):
    """Verify a password against its stored hash."""

    calculated_hash, _ = hash_password(password, salt)

    return hmac.compare_digest(
        calculated_hash,
        stored_hash
    )


def register_user(username, email, password):
    """Register a new student account."""

    username = username.strip()
    email = email.strip().lower()

    if len(username) < 3:
        return False, "Username must contain at least 3 characters."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    if "@" not in email or "." not in email:
        return False, "Please enter a valid email address."

    password_hash, salt = hash_password(password)

    conn = get_db_connection()

    try:
        conn.execute("""
            INSERT INTO users (
                username,
                email,
                password_hash,
                salt,
                role
            )
            VALUES (?, ?, ?, ?, 'student')
        """, (
            username,
            email,
            password_hash,
            salt
        ))

        conn.commit()

        return True, "Registration successful! You can now log in."

    except sqlite3.IntegrityError:
        return False, "Username or email already exists."

    except sqlite3.Error:
        return False, "Database error. Please try again."

    finally:
        conn.close()


def login_user(username, password):
    """Authenticate a user and return account information."""

    username = username.strip()

    conn = get_db_connection()

    try:
        user = conn.execute("""
            SELECT *
            FROM users
            WHERE username = ?
              AND is_active = 1
        """, (username,)).fetchone()

        if user is None:
            return False, "Invalid username or password.", None

        if not verify_password(
            password,
            user["password_hash"],
            user["salt"]
        ):
            return False, "Invalid username or password.", None

        user_data = {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }

        return True, "Login successful!", user_data

    finally:
        conn.close()


def set_login_session(user_data):
    """Store authenticated user information in Streamlit session."""

    st.session_state["authenticated"] = True
    st.session_state["user_id"] = user_data["id"]
    st.session_state["username"] = user_data["username"]
    st.session_state["email"] = user_data["email"]
    st.session_state["role"] = user_data["role"]


def logout_user():
    """Clear the current login session."""

    keys = [
        "authenticated",
        "user_id",
        "username",
        "email",
        "role",
        "current_quiz",
        "quiz_answers",
        "quiz_started_at"
    ]

    for key in keys:
        st.session_state.pop(key, None)


def is_logged_in():
    """Check whether a user is authenticated."""

    return (
        st.session_state.get("authenticated", False)
        and st.session_state.get("user_id") is not None
    )


def is_admin():
    """Check whether the authenticated user is an admin."""

    return (
        is_logged_in()
        and st.session_state.get("role") == "admin"
    )


def is_student():
    """Check whether the authenticated user is a student."""

    return (
        is_logged_in()
        and st.session_state.get("role") == "student"
    )


def require_login():
    """Stop access to protected pages without authentication."""

    if not is_logged_in():
        st.warning("Please log in to continue.")
        st.stop()


def require_admin():
    """Restrict admin functionality to authenticated admins."""

    require_login()

    if not is_admin():
        st.error("Access denied. Admin permission is required.")
        st.stop()


def get_current_user():
    """Return the currently logged-in user's information."""

    if not is_logged_in():
        return None

    return {
        "id": st.session_state.get("user_id"),
        "username": st.session_state.get("username"),
        "email": st.session_state.get("email"),
        "role": st.session_state.get("role")
    }
