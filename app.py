from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_NAME = "quiz.db"


# -----------------
# DATABASE HELPERS
# -----------------

def get_db():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# -----------------
# QUIZ DATA
# -----------------

QUIZZES = {
    "Quiz1": [
        {
            "question": "What is the capital of England?",
            "answers": ["Paris", "New York", "London"],
            "correct": "London"
        },
        {
            "question": "What is the capital of France?",
            "answers": ["Paris", "New York", "London"],
            "correct": "Paris"
        }
    ],
    "Quiz2": [
        {
            "question": "What is 1 + 1?",
            "answers": ["1", "2", "3"],
            "correct": "2"
        },
        {
            "question": "What is 2 + 2?",
            "answers": ["2", "3", "4"],
            "correct": "4"
        }
    ]
}


# -----------------
# ROUTES
# -----------------

@app.route("/")
def home():
    return render_template("home.html", user=session.get("user"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/resources")
def resources():
    return render_template("resources.html")


# -----------------
# AUTH
# -----------------

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = generate_password_hash(request.form["password"])

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "User already exists"

    conn.close()
    session["user"] = username
    return redirect(url_for("home"))


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[0], password):
        session["user"] = username
        return redirect(url_for("home"))

    return "Invalid credentials"


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


# -----------------
# QUIZ
# -----------------

@app.route("/quiz")
def quiz():
    return render_template("quizzes.html", quizzes=QUIZZES)


@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():
    if "user" not in session:
        return jsonify({"status": "error"})

    data = request.get_json()
    username = session["user"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"status": "error"})

    user_id = user[0]

    cursor.execute("""
        INSERT INTO quiz_results (user_id, score, total)
        VALUES (?, ?, ?)
    """, (user_id, data["score"], data["total"]))

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# -----------------
# REPORT
# -----------------

@app.route("/report")
def report():
    if "user" not in session:
        return redirect(url_for("home"))

    username = session["user"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return redirect(url_for("quiz"))

    user_id = user[0]

    cursor.execute("""
        SELECT score, total, date
        FROM quiz_results
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 1
    """, (user_id,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        return redirect(url_for("quiz"))

    score, total, date = result
    percentage = round((score / total) * 100, 2)

    return render_template(
        "report.html",
        score=score,
        total=total,
        date=date,
        percentage=percentage
    )

@app.route("/api/quiz/<quiz_name>")
def get_quiz(quiz_name):
    quiz = QUIZZES.get(quiz_name)
    return {"quiz": quiz}

# -----------------
# ACCOUNT
# -----------------

@app.route("/account")
def account():
    if "user" not in session:
        return redirect(url_for("home"))

    username = session["user"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return redirect(url_for("home"))

    user_id = user[0]

    cursor.execute("""
        SELECT score, total, date
        FROM quiz_results
        WHERE user_id = ?
        ORDER BY date DESC
    """, (user_id,))

    results = cursor.fetchall()
    conn.close()

    return render_template("account.html", username=username, results=results)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)