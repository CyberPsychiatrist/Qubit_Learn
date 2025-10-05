from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
from dotenv import load_dotenv

# Import database and API router
from vercel_backend.db import SupaDB
from .api import router as api_router

# ---------------- Setup ---------------- #
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

app = FastAPI(title="QubitLearn Backend")

# Enable Sessions
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "your-secret-key"))

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
db = SupaDB(
    url=os.getenv("SUPABASE_URL"),
    key=os.getenv("SUPABASE_KEY")
)

# Mount API router
app.include_router(api_router)

# Templates & Static files
app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(ROOT_DIR / "templates"))

# ---------------- Helpers ---------------- #
def require_login(request: Request):
    """Redirect user if not logged in"""
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return user


# ---------------- Routes ---------------- #

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Landing page"""
    user = request.session.get("user")
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("index.html", {"request": request})


# ---------- LOGIN ---------- #
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    """Handle user login via form."""
    try:
        user = db.sign_in(email=email, password=password)
    except Exception as e:
        print(f"Login error: {e}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Error connecting to server. Please try again."},
            status_code=400
        )

    if not user or "error" in user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password."},
            status_code=400
        )

    # ✅ Store session
    request.session["user"] = {"email": email, "id": user.get("id", "unknown")}
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


# ---------- SIGNUP ---------- #
@app.get("/signup", response_class=HTMLResponse)
def signup_form(request: Request):
    BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
async def signup_user(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...)
):
    """Handle user signup from form."""
    try:
        # Check if user already exists
        existing = db.get_user(email)
        if existing:
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "User with this email already exists."},
                status_code=400
            )

        # Create user in Supabase Auth
        new_user = db.signup_user(email, password, full_name)
        if not new_user or not hasattr(new_user, "user"):
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "Error creating user account."},
                status_code=400
            )

        user_id = new_user.user.id

        # Save user profile in your 'users' table
        db.save_user(user_id, email, username, full_name)

        # Redirect to login page with success message
        response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        request.session["flash"] = "Signup successful! Please log in."
        return response

    except Exception as e:
        print(f"Signup error: {e}")
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Something went wrong. Please try again."},
            status_code=500
        )


# ---------- DASHBOARD ---------- #
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: dict = Depends(require_login)):
    if isinstance(user, RedirectResponse):
        return user
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": user, "flash": flash}
    )


# ---------- OTHER ROUTES ---------- #
@app.get("/logout")
def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@app.get("/donate", response_class=HTMLResponse)
def donate(request: Request, user: dict = Depends(require_login)):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("donate.html", {"request": request, "user": user})


@app.get("/upload", response_class=HTMLResponse)
def upload(request: Request, user: dict = Depends(require_login)):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("upload.html", {"request": request, "user": user})


@app.get("/flashcards", response_class=HTMLResponse)
def flashcards(request: Request, user: dict = Depends(require_login)):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("flashcards.html", {"request": request, "user": user})


@app.get("/api/user")
def api_user(request: Request):
    user = request.session.get("user")
    if user:
        return JSONResponse({"user": user})
    return JSONResponse({"error": "Not logged in"}, status_code=401)
