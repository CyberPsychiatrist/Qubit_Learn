# frontend/main.py

from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import requests
from dotenv import load_dotenv
from functools import wraps

# ---------------- Setup ---------------- #

load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

# FastAPI backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ---------------- Helper Functions ---------------- #

def login_required(f):
    """Decorator to ensure user is logged in before accessing a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("⚠️ Please log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ---------------- Routes ---------------- #

@app.route("/")
def index():
    """Landing page or redirect to dashboard if logged in."""
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """User signup route."""
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        full_name = request.form.get("full_name")
        password = request.form.get("password")

        if not all([email, username, full_name, password]):
            flash("⚠️ Please fill in all fields.", "warning")
            return redirect(url_for("signup"))

        try:
            resp = requests.post(
                f"{BACKEND_URL}/signup",
                json={
                    "email": email,
                    "username": username,
                    "full_name": full_name,
                    "password": password
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if resp.status_code in (200, 201):
                flash("✅ Signup successful! Please check your email to verify your account.", "success")
                return redirect(url_for("login"))
            else:
                try:
                    err = resp.json().get("detail", resp.text)
                except Exception:
                    err = resp.text
                flash(f"❌ Signup failed: {err}", "danger")

        except requests.exceptions.RequestException as e:
            flash(f"❌ Unable to connect to backend: {e}", "danger")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login route."""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not all([email, password]):
            flash("⚠️ Please fill in both email and password.", "warning")
            return redirect(url_for("login"))

        try:
            resp = requests.post(
                f"{BACKEND_URL}/login",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if resp.status_code == 200:
                data = resp.json()
                session["user"] = {
                    "id": data.get("user_id"),
                    "email": email,
                    "username": data.get("username", ""),
                    "full_name": data.get("full_name", "")
                }
                flash("✅ Logged in successfully!", "success")
                return redirect(url_for("dashboard"))

            elif resp.status_code == 403:
                flash("⚠️ Please verify your email before logging in.", "warning")
            else:
                try:
                    err = resp.json().get("detail", resp.text)
                except Exception:
                    err = resp.text
                flash(f"❌ Login failed: {err}", "danger")

        except requests.exceptions.RequestException as e:
            flash(f"❌ Backend connection error: {e}", "danger")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    """Protected user dashboard."""
    return render_template("dashboard.html", user=session["user"])


@app.route("/donate")
@login_required
def donate():
    """Donation page (protected)."""
    return render_template("donate.html", user=session["user"])


@app.route("/upload")
@login_required
def upload():
    """Upload page (protected)."""
    return render_template("upload.html", user=session["user"])


@app.route("/flashcards")
@login_required
def flashcards():
    """Flashcards page (protected)."""
    return render_template("flashcards.html", user=session["user"])


@app.route("/logout")
def logout():
    """Clear session and log user out."""
    session.clear()
    flash("👋 You have been logged out.", "info")
    return redirect(url_for("index"))


# ---------------- Run App ---------------- #

if __name__ == "__main__":
    app.run(debug=True, port=5001)
