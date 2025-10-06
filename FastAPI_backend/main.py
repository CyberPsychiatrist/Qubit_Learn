
# main.py
from fastapi import Body
from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from pathlib import Path
import requests
import os
from FastAPI_backend.api import router as api_router
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Import DB
from FastAPI_backend.db import SupaDB

# IntaSend payment initiation endpoint
from services.intasend_client import intasend

# Base paths
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

# Initialize FastAPI app
app = FastAPI(title="QubitLearn Backend")
app.include_router(api_router)

# Middleware setup
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "your-secret-key"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database client
db = SupaDB(
    url=os.getenv("SUPABASE_URL"),
    key=os.getenv("SUPABASE_KEY"),
)

# Static + Templates setup
static_dir = FRONTEND_DIR / "static"
templates_dir = FRONTEND_DIR / "templates"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates = Jinja2Templates(directory=str(templates_dir))


# ------------------- HELPERS ------------------- #


def require_login(request: Request):
    """Ensure user is logged in, otherwise redirect to login."""
    user = request.session.get("user")
    print(f"[DEBUG] require_login session user: {user}")
    if not user:
        print("[DEBUG] User not logged in, redirecting to /login")
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return user

# Helper for IntaSend card payment using REST API
def create_card_checkout(email, amount, currency="KES", narrative="Donation"):
    url = "https://api.intasend.com/api/v1/checkout/"
    headers = {
        "Authorization": f"Bearer {os.getenv('INTASEND_SECRET_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "amount": amount,
        "currency": currency,
        "narrative": narrative
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# ------------------- ROUTES ------------------- #

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Landing page (redirects to dashboard if logged in)."""
    user = request.session.get("user")
    if user:
        return RedirectResponse(url="/dashboard")
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse("index.html", {"request": request, "flash": flash})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page."""
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse("login.html", {"request": request, "flash": flash})



@app.post("/login", response_class=HTMLResponse)
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    """Handle user login."""
    try:
        user = db.login_user(email, password)
        if not user or "id" not in user:
            print(f"[DEBUG] Login failed for {email}")
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Invalid credentials. Please try again."},
            )

        # Save session
        request.session["user"] = {
            "email": user["email"],
            "id": user["id"],
        }
        print(f"[DEBUG] Session after login: {request.session}")
        print(f"✅ User logged in: {user['email']}")

        # Redirect directly to dashboard
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    except Exception as e:
        print(f"❌ Login error: {e}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Login failed. Please try again."},
        )


@app.get("/signup", response_class=HTMLResponse)
def signup_form(request: Request):
    """Render signup page."""
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse("signup.html", {"request": request, "flash": flash})


@app.post("/signup", response_class=HTMLResponse)
async def signup_user(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...)
):
    """Handle user signup."""
    try:
        existing = db.get_user_by_email(email)
        if existing:
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "User with this email already exists."},
            )

        new_user = db.signup_user(email, password, full_name)
        if not new_user or not getattr(new_user, "user", None):
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "Error creating user account."},
            )

        db.save_user(new_user.user.id, email, username, full_name)
        print(f"✅ New user registered: {email}")

        # Redirect to login after signup
        request.session["flash"] = "Signup successful! Please log in."
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    except Exception as e:
        print(f"❌ Signup error: {e}")
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": str(e)},
        )


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user: dict = Depends(require_login)):
    """Protected dashboard route."""
    if isinstance(user, RedirectResponse):
        return user
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "flash": flash})

@app.get("/donate", response_class=HTMLResponse)
def dashboard(request: Request, user: dict = Depends(require_login)):
    """Protected dashboard route."""
    if isinstance(user, RedirectResponse):
        return user
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse("donate.html", {"request": request, "user": user, "flash": flash})


@app.get("/api/user")
def get_current_user(request: Request):
    """Return currently logged-in user."""
    user = request.session.get("user")
    if not user:
        return JSONResponse(status_code=404, content={"detail": "Not logged in"})
    return {"user": user}


@app.get("/logout")
def logout(request: Request):
    """Logout and redirect to login."""
    request.session.pop("user", None)
    request.session["flash"] = "You have been logged out."
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


# Flashcards page
@app.get("/flashcards", response_class=HTMLResponse)
def flashcards_page(request: Request, user: dict = Depends(require_login)):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("flashcards.html", {"request": request, "user": user})


@app.post("/api/flashcards")
async def api_add_flashcards(request: Request):
    try:
        rows = await request.json()
        if isinstance(rows, dict):
            rows = [rows]
        success, result = db.insert_cards(rows)
        if success:
            return {"ok": True, "data": result}
        return {"ok": False, "error": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/add-flashcard", response_class=HTMLResponse)
def add_flashcard_page(request: Request, user: dict = Depends(require_login)):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("add_flashcard.html", {"request": request, "user": user})

# API endpoint to get all flashcards (GET, no body required)
@app.get("/api/flashcards")
async def api_get_flashcards():
    try:
        cards = db.client.table("cards").select("*").execute()
        return {"flashcards": getattr(cards, "data", [])}
    except Exception as e:
        return {"flashcards": [], "error": str(e)}
    
# Upload page
@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request, user: dict = Depends(require_login)):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("upload.html", {"request": request, "user": user})

# Paraphraser page
@app.get("/paraphraser", response_class=HTMLResponse)
def paraphraser_page(request: Request, user: dict = Depends(require_login)):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("paraphraser.html", {"request": request, "user": user})

# IntaSend payment initiation endpoint
@app.post("/api/initiate_payment")
async def initiate_payment(
    request: Request,
    amount: float = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    method: str = Form(...)
):
    """Initiate IntaSend card or M-Pesa STK payment."""
    try:
        if method == "card":
            resp = create_card_checkout(email=email, amount=amount, currency="KES", narrative="Donation")
            return {"checkout_url": resp.get("url")}
        elif method == "mpesa":
            if not phone:
                return {"error": "Phone number required for M-Pesa payments."}
            resp = intasend.collect.mpesa_stk_push(
                phone_number=phone,
                amount=amount,
                currency="KES",
                narrative="Donation"
            )
            return {"status": resp["status"], "invoice_id": resp["invoice_id"]}
        else:
            return {"error": "Invalid payment method."}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "QubitLearn Backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
