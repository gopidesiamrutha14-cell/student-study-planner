
from flask import Flask, request, jsonify, send_from_directory
import mysql.connector
from datetime import datetime
import os


# Frontend folder path
FRONTEND_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend")
)

app = Flask(__name__)


# Connect to MySQL database
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin",
        database="student_study_planner"
    )


# Validate a date in YYYY-MM-DD format
def is_valid_date(value):
    if not isinstance(value, str):
        return False

    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# Serve the frontend home page
@app.route("/")
def home():
    return send_from_directory(FRONTEND_FOLDER, "index.html")


# Serve CSS and JavaScript files
@app.route("/<path:filename>")
def frontend_files(filename):
    if filename in ("style.css", "script.js"):
        return send_from_directory(FRONTEND_FOLDER, filename)

    return jsonify({"error": "File not found."}), 404


# Test database connection
@app.route("/test-db", methods=["GET"])
def test_db():
    connection = None

    try:
        connection = get_db_connection()

        return jsonify({
            "message": "MySQL database connected successfully!"
        })

    except mysql.connector.Error:
        app.logger.exception("Database connection failed")
        return jsonify({
            "error": "Could not connect to the database."
        }), 500

    finally:
        if connection is not None and connection.is_connected():
            connection.close()


# Add a study task
@app.route("/tasks", methods=["POST"])
def add_task():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Please send valid task details."}), 400

    task_name = data.get("task_name")
    subject = data.get("subject")
    deadline = data.get("deadline")
    user_id = data.get("user_id")

    if not isinstance(task_name, str) or not task_name.strip():
        return jsonify({"error": "Task name is required."}), 400

    if not isinstance(subject, str) or not subject.strip():
        return jsonify({"error": "Subject is required."}), 400

    if not is_valid_date(deadline):
        return jsonify({
            "error": "Enter a valid deadline in YYYY-MM-DD format."
        }), 400

    if (
        isinstance(user_id, bool)
        or not isinstance(user_id, int)
        or user_id <= 0
    ):
        return jsonify({"error": "A valid user ID is required."}), 400

    task_name = task_name.strip()
    subject = subject.strip()

    if len(task_name) > 150 or len(subject) > 100:
        return jsonify({
            "error": "Task name or subject is too long."
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO tasks (user_id, task_name, subject, deadline)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, task_name, subject, deadline)
        )

        connection.commit()

        return jsonify({
            "message": "Study task added successfully!",
            "task_id": cursor.lastrowid
        }), 201

    except mysql.connector.Error:
        if connection is not None and connection.is_connected():
            connection.rollback()

        app.logger.exception("Could not add study task")
        return jsonify({
            "error": "Could not add the study task. Check the details and database."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# View tasks for a student
@app.route("/tasks/<int:user_id>", methods=["GET"])
def get_tasks(user_id):
    if user_id <= 0:
        return jsonify({"error": "Invalid user ID."}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT task_id, user_id, task_name, subject,
                   deadline, status, created_at
            FROM tasks
            WHERE user_id = %s
            ORDER BY deadline ASC
            """,
            (user_id,)
        )

        tasks = cursor.fetchall()

        for task in tasks:
            if task["deadline"]:
                task["deadline"] = task["deadline"].isoformat()

            if task["created_at"]:
                task["created_at"] = task["created_at"].isoformat()

        return jsonify(tasks)

    except mysql.connector.Error:
        app.logger.exception("Could not load study tasks")
        return jsonify({"error": "Could not load study tasks."}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# Mark a task as completed
@app.route("/tasks/<int:task_id>/complete", methods=["PUT"])
def complete_task(task_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE tasks
            SET status = 'Completed'
            WHERE task_id = %s
            """,
            (task_id,)
        )

        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Task not found or already completed."}), 404

        return jsonify({
            "message": "Task marked as completed!"
        })

    except mysql.connector.Error:
        if connection is not None and connection.is_connected():
            connection.rollback()

        app.logger.exception("Could not complete study task")
        return jsonify({"error": "Could not update the task."}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# Delete a study task
@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM tasks WHERE task_id = %s",
            (task_id,)
        )

        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Task not found."}), 404

        return jsonify({
            "message": "Study task deleted successfully!"
        })

    except mysql.connector.Error:
        if connection is not None and connection.is_connected():
            connection.rollback()

        app.logger.exception("Could not delete study task")
        return jsonify({"error": "Could not delete the task."}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# Add a study session
@app.route("/sessions", methods=["POST"])
def add_session():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Please send valid study session details."
        }), 400

    user_id = data.get("user_id")
    subject = data.get("subject")
    study_date = data.get("study_date")
    duration = data.get("duration_minutes")
    notes = data.get("notes", "")

    if (
        isinstance(user_id, bool)
        or not isinstance(user_id, int)
        or user_id <= 0
    ):
        return jsonify({"error": "A valid user ID is required."}), 400

    if not isinstance(subject, str) or not subject.strip():
        return jsonify({"error": "Subject is required."}), 400

    if len(subject.strip()) > 100:
        return jsonify({"error": "Subject is too long."}), 400

    if not is_valid_date(study_date):
        return jsonify({
            "error": "Enter a valid study date in YYYY-MM-DD format."
        }), 400

    if isinstance(duration, bool):
        return jsonify({
            "error": "Duration must be a positive whole number of minutes."
        }), 400

    try:
        duration = int(duration)

        if duration <= 0:
            raise ValueError

    except (TypeError, ValueError):
        return jsonify({
            "error": "Duration must be a positive whole number of minutes."
        }), 400

    if isinstance(data.get("duration_minutes"), float):
        return jsonify({
            "error": "Duration must be a whole number of minutes."
        }), 400

    if not isinstance(notes, str):
        return jsonify({"error": "Notes must be text."}), 400

    subject = subject.strip()
    notes = notes.strip()

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO study_sessions
                (user_id, subject, study_date, duration_minutes, notes)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, subject, study_date, duration, notes)
        )

        connection.commit()

        return jsonify({
            "message": "Study session saved successfully!",
            "session_id": cursor.lastrowid
        }), 201

    except mysql.connector.Error:
        if connection is not None and connection.is_connected():
            connection.rollback()

        app.logger.exception("Could not save study session")
        return jsonify({
            "error": "Could not save the study session. Check the details and database."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# View study sessions for a student
@app.route("/sessions/<int:user_id>", methods=["GET"])
def get_sessions(user_id):
    if user_id <= 0:
        return jsonify({"error": "Invalid user ID."}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT session_id, user_id, subject, study_date,
                   duration_minutes, notes, created_at
            FROM study_sessions
            WHERE user_id = %s
            ORDER BY study_date DESC, session_id DESC
            """,
            (user_id,)
        )

        sessions = cursor.fetchall()

        for session in sessions:
            if session["study_date"]:
                session["study_date"] = session["study_date"].isoformat()

            if session["created_at"]:
                session["created_at"] = session["created_at"].isoformat()

        return jsonify(sessions)

    except mysql.connector.Error:
        app.logger.exception("Could not load study sessions")
        return jsonify({"error": "Could not load study sessions."}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# Dashboard summary
@app.route("/dashboard/<int:user_id>", methods=["GET"])
def dashboard(user_id):
    if user_id <= 0:
        return jsonify({"error": "Invalid user ID."}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_tasks,
                COALESCE(
                    SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END),
                    0
                ) AS pending_tasks,
                COALESCE(
                    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END),
                    0
                ) AS completed_tasks
            FROM tasks
            WHERE user_id = %s
            """,
            (user_id,)
        )

        task_summary = cursor.fetchone()

        cursor.execute(
            """
            SELECT COALESCE(SUM(duration_minutes), 0)
                   AS total_study_minutes
            FROM study_sessions
            WHERE user_id = %s
            """,
            (user_id,)
        )

        study_summary = cursor.fetchone()

        return jsonify({
            "total_tasks": task_summary["total_tasks"],
            "pending_tasks": task_summary["pending_tasks"],
            "completed_tasks": task_summary["completed_tasks"],
            "total_study_minutes": study_summary["total_study_minutes"]
        })

    except mysql.connector.Error:
        app.logger.exception("Could not load dashboard")
        return jsonify({"error": "Could not load dashboard data."}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# Start Flask
if __name__ == "__main__":
    app.run(debug=True)
