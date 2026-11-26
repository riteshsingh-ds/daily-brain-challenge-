
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

# Database location
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "brain_challenge.db"


def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all required database tables."""

    conn = get_db_connection()

    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student'
                CHECK(role IN ('student', 'admin')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT,
            difficulty TEXT NOT NULL
                CHECK(difficulty IN ('Easy', 'Medium', 'Hard')),
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL
                CHECK(correct_option IN ('A', 'B', 'C', 'D')),
            explanation TEXT,
            source TEXT DEFAULT 'Admin',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (created_by) REFERENCES users(id)
                ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            total_questions INTEGER NOT NULL,
            correct_answers INTEGER NOT NULL DEFAULT 0,
            score REAL NOT NULL DEFAULT 0,
            accuracy REAL NOT NULL DEFAULT 0,
            time_taken INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS quiz_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL,
            question_id INTEGER,
            question_text TEXT NOT NULL,
            selected_option TEXT,
            correct_option TEXT NOT NULL,
            is_correct INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id)
                ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions(id)
                ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            certificate_id TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            attempt_id INTEGER NOT NULL UNIQUE,
            total_questions INTEGER NOT NULL,
            correct_answers INTEGER NOT NULL,
            accuracy REAL NOT NULL,
            issued_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'valid'
                CHECK(status IN ('valid', 'revoked')),
            revoked_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE,
            UNIQUE(user_id, subject)
        );

        CREATE INDEX IF NOT EXISTS idx_certificates_user
        ON certificates(user_id);

        CREATE INDEX IF NOT EXISTS idx_certificates_subject
        ON certificates(subject);

        CREATE INDEX IF NOT EXISTS idx_questions_subject
        ON questions(subject);

        CREATE INDEX IF NOT EXISTS idx_questions_difficulty
        ON questions(difficulty);

        CREATE INDEX IF NOT EXISTS idx_attempts_user
        ON quiz_attempts(user_id);

        CREATE INDEX IF NOT EXISTS idx_attempts_created
        ON quiz_attempts(created_at);
        """)

        conn.commit()

    finally:
        conn.close()


def add_question(data, created_by=None):
    """Insert one question into the question bank."""

    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            INSERT INTO questions (
                subject, topic, difficulty, question,
                option_a, option_b, option_c, option_d,
                correct_option, explanation, source, created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["subject"],
            data.get("topic", ""),
            data["difficulty"],
            data["question"],
            data["option_a"],
            data["option_b"],
            data["option_c"],
            data["option_d"],
            data["correct_option"].upper(),
            data.get("explanation", ""),
            data.get("source", "Admin"),
            created_by
        ))

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def get_questions(subject=None, difficulty=None, limit=None):
    """Fetch active questions with optional filters."""

    conn = get_db_connection()

    try:
        query = "SELECT * FROM questions WHERE is_active = 1"
        params = []

        if subject and subject != "All":
            query += " AND subject = ?"
            params.append(subject)

        if difficulty and difficulty != "All":
            query += " AND difficulty = ?"
            params.append(difficulty)

        query += " ORDER BY RANDOM()"

        if limit is not None:
            query += " LIMIT ?"
            params.append(max(1, int(limit)))

        return [
            dict(row) for row in
            conn.execute(query, params).fetchall()
        ]

    finally:
        conn.close()


def get_subjects():
    """Return all subjects containing active questions."""

    conn = get_db_connection()

    try:
        rows = conn.execute("""
            SELECT DISTINCT subject
            FROM questions
            WHERE is_active = 1
            ORDER BY subject
        """).fetchall()

        return [row["subject"] for row in rows]

    finally:
        conn.close()


def save_quiz_attempt(
    user_id,
    subject,
    difficulty,
    answers,
    time_taken=0
):
    """
    Save a completed quiz and its individual answers.

    Each answer should contain:
    question_id, question_text,
    selected_option, correct_option.
    """

    total = len(answers)

    if total == 0:
        raise ValueError("A quiz must contain at least one answer.")

    correct = sum(
        1 for answer in answers
        if (answer.get("selected_option") or "").upper()
        == answer["correct_option"].upper()
    )

    accuracy = round((correct / total) * 100, 2)

    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            INSERT INTO quiz_attempts (
                user_id, subject, difficulty,
                total_questions, correct_answers,
                score, accuracy, time_taken
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            subject,
            difficulty,
            total,
            correct,
            correct,
            accuracy,
            max(0, int(time_taken))
        ))

        attempt_id = cursor.lastrowid

        for answer in answers:
            selected = (
                answer.get("selected_option") or ""
            ).upper()

            correct_option = answer["correct_option"].upper()

            is_correct = int(selected == correct_option)

            conn.execute("""
                INSERT INTO quiz_answers (
                    attempt_id, question_id, question_text,
                    selected_option, correct_option, is_correct
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                attempt_id,
                answer.get("question_id"),
                answer.get("question_text", ""),
                selected,
                correct_option,
                is_correct
            ))

        conn.commit()
        return attempt_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def get_user_attempts(user_id, limit=50):
    """Get recent quiz attempts for a user."""

    conn = get_db_connection()

    try:
        rows = conn.execute("""
            SELECT *
            FROM quiz_attempts
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
        """, (user_id, max(1, int(limit)))).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


def get_leaderboard(limit=10):
    """Get leaderboard based on total correct answers."""

    conn = get_db_connection()

    try:
        rows = conn.execute("""
            SELECT
                u.id,
                u.username,
                COUNT(a.id) AS quizzes_played,
                COALESCE(SUM(a.correct_answers), 0)
                    AS total_correct,
                COALESCE(ROUND(AVG(a.accuracy), 2), 0)
                    AS average_accuracy
            FROM users u
            LEFT JOIN quiz_attempts a ON u.id = a.user_id
            WHERE u.is_active = 1
              AND u.role = 'student'
            GROUP BY u.id, u.username
            ORDER BY total_correct DESC,
                     average_accuracy DESC,
                     quizzes_played DESC
            LIMIT ?
        """, (max(1, int(limit)),)).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


def get_user_statistics(user_id):
    """Get summary statistics for a student's dashboard."""

    conn = get_db_connection()

    try:
        row = conn.execute("""
            SELECT
                COUNT(*) AS total_quizzes,
                COALESCE(SUM(total_questions), 0)
                    AS questions_attempted,
                COALESCE(SUM(correct_answers), 0)
                    AS total_correct,
                COALESCE(ROUND(AVG(accuracy), 2), 0)
                    AS average_accuracy,
                COALESCE(MAX(score), 0) AS best_score
            FROM quiz_attempts
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        return dict(row)

    finally:
        conn.close()


def get_admin_statistics():
    """Get platform statistics for the admin dashboard."""

    conn = get_db_connection()

    try:
        users = conn.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE role = 'student'
        """).fetchone()["total"]

        admins = conn.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE role = 'admin'
        """).fetchone()["total"]

        questions = conn.execute("""
            SELECT COUNT(*) AS total
            FROM questions
            WHERE is_active = 1
        """).fetchone()["total"]

        attempts = conn.execute("""
            SELECT COUNT(*) AS total
            FROM quiz_attempts
        """).fetchone()["total"]

        return {
            "total_students": users,
            "total_admins": admins,
            "total_questions": questions,
            "total_attempts": attempts
        }

    finally:
        conn.close()


def deactivate_question(question_id):
    """Deactivate a question without deleting its history."""

    conn = get_db_connection()

    try:
        conn.execute("""
            UPDATE questions
            SET is_active = 0
            WHERE id = ?
        """, (question_id,))

        conn.commit()

    finally:
        conn.close()


# Initialize the database when this module is imported.
init_db()


# ==========================================
# CERTIFICATE MANAGEMENT
# ==========================================

def create_certificate(user_id, subject, attempt_id, total_questions, correct_answers, accuracy):
    """Create one permanent certificate per student and subject."""
    import secrets
    import re
    from datetime import datetime

    if int(total_questions) < 20 or float(accuracy) < 70:
        return None

    slug = re.sub(r"[^A-Z0-9]", "", str(subject).upper())[:3] or "GEN"
    year = datetime.now().year
    certificate_id = f"DBC-{slug}-{year}-{secrets.token_hex(3).upper()}"
    conn = get_db_connection()
    try:
        existing = conn.execute(
            "SELECT * FROM certificates WHERE user_id = ? AND subject = ?",
            (user_id, subject)
        ).fetchone()
        if existing:
            return dict(existing)
        conn.execute("""
            INSERT INTO certificates (
                certificate_id, user_id, subject, attempt_id,
                total_questions, correct_answers, accuracy
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            certificate_id, user_id, subject, attempt_id,
            int(total_questions), int(correct_answers), float(accuracy)
        ))
        conn.commit()
        row = conn.execute(
            "SELECT * FROM certificates WHERE certificate_id = ?",
            (certificate_id,)
        ).fetchone()
        return dict(row) if row else None
    except sqlite3.IntegrityError:
        conn.rollback()
        row = conn.execute(
            "SELECT * FROM certificates WHERE user_id = ? AND subject = ?",
            (user_id, subject)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_certificates(user_id):
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT c.*, u.username
            FROM certificates c
            JOIN users u ON u.id = c.user_id
            WHERE c.user_id = ?
            ORDER BY c.issued_at DESC, c.id DESC
        """, (user_id,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_certificate(certificate_id):
    conn = get_db_connection()
    try:
        row = conn.execute("""
            SELECT c.*, u.username, u.email
            FROM certificates c
            JOIN users u ON u.id = c.user_id
            WHERE c.certificate_id = ?
        """, (certificate_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_certificates():
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT c.*, u.username
            FROM certificates c
            JOIN users u ON u.id = c.user_id
            ORDER BY c.issued_at DESC, c.id DESC
        """).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def revoke_certificate(certificate_id):
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            UPDATE certificates
            SET status = 'revoked', revoked_at = CURRENT_TIMESTAMP
            WHERE certificate_id = ? AND status = 'valid'
        """, (certificate_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
