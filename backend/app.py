
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
import logging

app = Flask(
    __name__,
    static_folder="../frontend",
    static_url_path=""
)

CORS(app)
logging.basicConfig(level=logging.INFO)


# Connect to hosted Aiven MySQL
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "15835")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "defaultdb"),
        ssl_disabled=False,
        connection_timeout=15
    )


# Return database errors as JSON instead of HTML
@app.errorhandler(mysql.connector.Error)
def handle_database_error(error):
    app.logger.exception("Database operation failed")
    return jsonify({
        "error": "Database operation failed. Check the Render logs."
    }), 500


# Open frontend homepage
@app.route("/")
def home():
    return app.send_static_file("index.html")


# Optional health check
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# Get all study tasks
@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT task_id, task_name, subject, deadline, status
            FROM tasks
            ORDER BY task_id DESC
        """)

        tasks = cursor.fetchall()

        for task in tasks:
            if task.get("deadline"):
                task["deadline"] = str(task["deadline"])

        return jsonify(tasks)

    finally:
        cursor.close()
        conn.close()


# Add a new study task
@app.route("/api/tasks", methods=["POST"])
def add_task():
    data = request.get_json(silent=True) or {}

    task_name = data.get("task_name")
    subject = data.get("subject", "")
    deadline = data.get("deadline") or None

    if not isinstance(task_name, str) or not task_name.strip():
        return jsonify({
            "error": "Task name is required"
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO tasks (task_name, subject, deadline, status)
            VALUES (%s, %s, %s, 'Pending')
        """, (task_name.strip(), subject, deadline))

        conn.commit()

        return jsonify({
            "message": "Task added successfully",
            "task_id": cursor.lastrowid
        }), 201

    finally:
        cursor.close()
        conn.close()


# Update task status
@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    if status not in ["Pending", "Completed"]:
        return jsonify({
            "error": "Invalid status"
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE tasks SET status = %s WHERE task_id = %s",
            (status, task_id)
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Task not found"
            }), 404

        return jsonify({
            "message": "Task updated successfully"
        })

    finally:
        cursor.close()
        conn.close()


# Delete a study task
@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM tasks WHERE task_id = %s",
            (task_id,)
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Task not found"
            }), 404

        return jsonify({
            "message": "Task deleted successfully"
        })

    finally:
        cursor.close()
        conn.close()


# Dashboard statistics
@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                COUNT(*) AS totalTasks,
                COALESCE(SUM(status = 'Pending'), 0) AS pendingTasks,
                COALESCE(SUM(status = 'Completed'), 0) AS completedTasks
            FROM tasks
        """)

        result = cursor.fetchone()
        return jsonify(result)

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False
    )
