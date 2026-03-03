from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

users = {}
quiz_results = []

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]

    if username in users:
        return "User already exists"

    users[username] = password
    session["user"] = username
    return redirect(url_for("home"))

@app.route("/")
def home():
    return render_template("home.html", user=session.get("user"))

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/resources")
def resources():
    return render_template("resources.html")

@app.route("/news")
def news():
    return render_template("news.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")



@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    if username in users and users[username] == password:
        session["user"] = username
        return redirect(url_for("home"))

    return "Invalid credentials"

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route("/quiz")
def quiz():
    return render_template("quizzes.html")

# # Quiz page
# @app.route("/quizzes")
# def quizzes():
#     return render_template("quizzes.html")


# Quiz report page
@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():
    data = request.get_json()

    result = {
        "username": session.get("user"),
        "score": data["score"],
        "total": data["total"],
        "date": datetime.now()
    }

    quiz_results.append(result)
    session["last_result"] = result

    return {"status": "success"}

# Report pag
@app.route("/report")
def report():
    result = session.get("last_result")
    if not result:
        return redirect(url_for("quiz"))

    result_percentage = (result["score"] / result["total"]) * 100
    result_percentage_str = f"{result_percentage}%"

    return render_template(
        "report.html",
        result=result,
        result_percentage=result_percentage_str
    )


if __name__ == "__main__":
    app.run(debug=True)