from flask import Flask, request, jsonify
import sqlite3
import os
from logger import setup_logger

app = Flask(__name__)
logger = setup_logger("UserAPI")
DB_PATH = os.getenv("USER_DB", "users.db")

def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
    conn.commit()
    conn.close()

def reset_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    conn.commit()
    conn.close()

@app.route("/add_user", methods=["POST"])
def add_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    logger.info(f"Add user attempt: {username}")

    if not username or not password:
        logger.warning("Missing credentials in /add_user")
        return jsonify({"message": "Missing credentials"}), 400

    for _ in range(5):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            logger.info(f"User added: {username}")
            return jsonify({"message": "User added"}), 201
        except sqlite3.IntegrityError:
            logger.warning(f"User already exists: {username}")
            return jsonify({"message": "User already exists"}), 400
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                import time
                logger.warning("Database locked, retrying...")
                time.sleep(0.1)
                continue
            logger.error(f"OperationalError on add_user: {e}")
            return jsonify({"message": str(e)}), 500
        except Exception as e:
            logger.error(f"Unexpected error on add_user: {e}")
            return jsonify({"message": f"Unexpected error: {e}"}), 500

    logger.error("DB locked: retries exceeded")
    return jsonify({"message": "Database is locked. Retry later."}), 503

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]
    logger.info(f"Login attempt for user: {username}")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        logger.warning(f"Login failed: user not found - {username}")
        return jsonify({"message": "User not found"}), 404
    elif row[0] == password:
        logger.info(f"Login successful: {username}")
        return jsonify({"message": "Login successful"}), 200
    else:
        logger.warning(f"Incorrect password for user: {username}")
        return jsonify({"message": "Incorrect password"}), 401

@app.route("/get_user", methods=["GET"])
def get_user():
    username = request.args.get("username")
    logger.info(f"Fetching user: {username}")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        logger.info(f"User found: {username}")
        return jsonify({"username": row[0], "password": row[1]}), 200
    logger.warning(f"User not found: {username}")
    return jsonify({"message": "User not found"}), 404

@app.route("/delete_user", methods=["DELETE"])
def delete_user():
    data = request.get_json()
    username = data["username"]
    logger.info(f"Delete attempt for user: {username}")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    result = cursor.rowcount
    conn.close()

    if result > 0:
        logger.info(f"User deleted: {username}")
        return jsonify({"message": "User deleted"}), 200
    logger.warning(f"Delete failed: user not found - {username}")
    return jsonify({"message": "User not found"}), 404

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    init_db()
    app.run(debug=False, use_reloader=False)
