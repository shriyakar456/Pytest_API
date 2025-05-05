from flask import Flask, request, jsonify
import sqlite3, os
from dotenv import load_dotenv

load_dotenv()  # ✅ Load environment variables from .env

app = Flask(__name__)
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
    if not username or not password:
        return jsonify({"message": "Missing credentials"}), 400

    for _ in range(5):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return jsonify({"message": "User added"}), 201
        except sqlite3.IntegrityError:
            return jsonify({"message": "User already exists"}), 400
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                import time
                time.sleep(0.1)
                continue
            return jsonify({"message": str(e)}), 500
        except Exception as e:
            return jsonify({"message": f"Unexpected error: {e}"}), 500
    return jsonify({"message": "Database is locked. Retry later."}), 503

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return jsonify({"message": "User not found"}), 404
    elif row[0] == password:
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Incorrect password"}), 401

@app.route("/get_user", methods=["GET"])
def get_user():
    username = request.args.get("username")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({"username": row[0], "password": row[1]}), 200
    return jsonify({"message": "User not found"}), 404

@app.route("/delete_user", methods=["DELETE"])
def delete_user():
    data = request.get_json()
    username = data["username"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    result = cursor.rowcount
    conn.close()
    if result > 0:
        return jsonify({"message": "User deleted"}), 200
    return jsonify({"message": "User not found"}), 404

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    init_db()
    app.run(debug=False, use_reloader=False)
