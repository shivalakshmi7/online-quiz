
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-to-a-long-random-secret-key"

# DATABASE
def get_db():
    conn = sqlite3.connect("quiz.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# QUIZ DATA
quiz_data = {
    "python": {
        "title": "Python Programming",
        "questions": [
            {"question": "What is Python?", "options": {"A": "Programming Language", "B": "Operating System", "C": "Browser"}, "answer": "A"},
            {"question": "Which symbol is used for comments?", "options": {"A": "//", "B": "#", "C": "*"}, "answer": "B"},
            {"question": "Which function displays output?", "options": {"A": "input()", "B": "print()", "C": "display()"}, "answer": "B"},
            {"question": "Which data type stores True or False?", "options": {"A": "int", "B": "str", "C": "bool"}, "answer": "C"},
            {"question": "Which keyword defines a function?", "options": {"A": "function", "B": "def", "C": "define"}, "answer": "B"},
            {"question": "Which brackets create a list?", "options": {"A": "[]", "B": "{}", "C": "()"}, "answer": "A"},
            {"question": "Which operator checks equality?", "options": {"A": "=", "B": "==", "C": "!="}, "answer": "B"},
            {"question": "Which keyword is used for a loop?", "options": {"A": "repeat", "B": "loop", "C": "for"}, "answer": "C"},
            {"question": "Which function gets user input?", "options": {"A": "input()", "B": "print()", "C": "scan()"}, "answer": "A"},
            {"question": "Which extension is used for Python files?", "options": {"A": ".html", "B": ".py", "C": ".css"}, "answer": "B"}
        ]
    },

    "html_css": {
        "title": "HTML and CSS",
        "questions": [
            {"question": "What does HTML stand for?", "options": {"A": "Hyper Text Markup Language", "B": "High Text Machine Language", "C": "Home Tool Markup Language"}, "answer": "A"},
            {"question": "Which tag creates a paragraph?", "options": {"A": "<h1>", "B": "<p>", "C": "<div>"}, "answer": "B"},
            {"question": "Which tag creates a hyperlink?", "options": {"A": "<a>", "B": "<link>", "C": "<href>"}, "answer": "A"},
            {"question": "Which property changes text color?", "options": {"A": "background", "B": "font-size", "C": "color"}, "answer": "C"},
            {"question": "Which language styles web pages?", "options": {"A": "Python", "B": "CSS", "C": "SQL"}, "answer": "B"},
            {"question": "Which tag inserts an image?", "options": {"A": "<img>", "B": "<image>", "C": "<picture-link>"}, "answer": "A"},
            {"question": "Which CSS property changes background color?", "options": {"A": "color", "B": "background-color", "C": "font-color"}, "answer": "B"},
            {"question": "Which symbol selects a class in CSS?", "options": {"A": "#", "B": "*", "C": "."}, "answer": "C"},
            {"question": "Which tag creates an unordered list?", "options": {"A": "<ul>", "B": "<ol>", "C": "<li>"}, "answer": "A"},
            {"question": "Which CSS property controls text size?", "options": {"A": "text-style", "B": "font-size", "C": "size"}, "answer": "B"}
        ]
    }
}


# HOME
@app.route("/")
def home():
    return redirect(url_for("login"))


# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email:
            flash("Please enter your name and email.")

        elif len(password) < 8:
            flash("Password must contain at least 8 characters.")

        elif password != confirm:
            flash("Passwords do not match.")

        else:
            conn = get_db()

            try:
                hashed = generate_password_hash(password)

                conn.execute(
                    "INSERT INTO users (name,email,password) VALUES (?,?,?)",
                    (name, email, hashed)
                )

                conn.commit()
                flash("Registration successful! Please login.")
                return redirect(url_for("login"))

            except sqlite3.IntegrityError:
                flash("Email already registered.")

            finally:
                conn.close()

    return render_template("register.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            return redirect(url_for("quizzes"))

        flash("Invalid email or password.")

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# QUIZ LIST
@app.route("/quizzes")
def quizzes():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("quizzes.html", name=session["name"])


# START AND SUBMIT QUIZ
@app.route("/quiz/<subject>", methods=["GET", "POST"])
def quiz(subject):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if subject not in quiz_data:
        return redirect(url_for("quizzes"))

    current = quiz_data[subject]
    questions = current["questions"]

    if request.method == "POST":

        score = 0
        answers = []

        for i, question in enumerate(questions, start=1):
            selected = request.form.get(f"q{i}", "")
            correct = question["answer"]

            is_correct = selected == correct

            if is_correct:
                score += 1

            answers.append({
                "question": question["question"],
                "selected": question["options"].get(selected, "Not answered"),
                "correct": question["options"][correct],
                "is_correct": is_correct
            })

        total = len(questions)

        session["score"] = score
        session["total"] = total
        session["answers"] = answers
        session["subject"] = subject

        return redirect(url_for("result"))

    return render_template(
        "quiz.html",
        title=current["title"],
        questions=questions,
        duration=15
    )


# RESULT
@app.route("/result")
def result():

    if "user_id" not in session or "score" not in session:
        return redirect(url_for("quizzes"))

    score = session["score"]
    total = session["total"]
    percentage = round((score / total) * 100, 2)

    return render_template(
        "result.html",
        score=score,
        total=total,
        percentage=percentage
    )


# REVIEW ANSWERS
@app.route("/review")
def review():

    if "user_id" not in session or "answers" not in session:
        return redirect(url_for("quizzes"))

    return render_template(
        "review.html",
        answers=session["answers"]
    )


# RUN APPLICATION
if __name__ == "__main__":
    create_table()
    app.run(debug=True)
