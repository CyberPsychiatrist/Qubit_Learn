
# main.py
from fastapi import Body
from fastapi import FastAPI, Request, Form, Depends, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import BaseModel, EmailStr, Field
import requests
import os
import re
from api import router as api_router
from dotenv import load_dotenv
from intasend import APIService


# Load environment variables
load_dotenv()

# Import DB
from db import SupaDB

# IntaSend credentials
INTASEND_SECRET_TOKEN = os.getenv("INTASEND_SECRET_TOKEN")
INTASEND_PUBLISHABLE_KEY = os.getenv("INTASEND_PUBLISHABLE_KEY")
TEST_MODE = os.getenv("INTASEND_TEST_MODE", "true").lower() in ("1", "true", "yes")

if not INTASEND_SECRET_TOKEN or not INTASEND_PUBLISHABLE_KEY:
    raise RuntimeError("Missing IntaSend credentials in environment variables.")

# Initialize IntaSend SDK
service = APIService(
    token=INTASEND_SECRET_TOKEN,
    publishable_key=INTASEND_PUBLISHABLE_KEY,
    test=TEST_MODE,
)

# Sanitize API reference helper
def sanitize_api_ref(text: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_\- ]", "-", text)
    return clean[:30]


# Base paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# For frontend static files (CSS, JS)
FRONTEND_STATIC_DIR = BASE_DIR / "frontend" / "static"

# Pydantic models for requests
class STKDonationRequest(BaseModel):
    email: EmailStr
    phone: str = Field(..., pattern=r"^2547\d{8}$", description="Safaricom MSISDN format e.g. 254712345678")
    amount: float = Field(gt=0)
    note: str = None
    currency: str = "KES"

class CheckoutDonationRequest(BaseModel):
    email: EmailStr
    amount: float = Field(gt=0)
    currency: str = Field(default="KES", description="Currency code")

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
static_dir = FRONTEND_STATIC_DIR
templates_dir = TEMPLATES_DIR

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
        # Check for existing email
        existing_email = db.get_user_by_email(email)
        if existing_email:
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "User with this email already exists."},
            )

        # Check for existing username
        try:
            existing_username = db.client.table("users").select("id").eq("username", username).limit(1).execute()
            if existing_username.data:
                return templates.TemplateResponse(
                    "signup.html",
                    {"request": request, "error": "Username is already taken. Please choose another."},
                )
        except Exception as e:
            print(f"❌ Error checking username: {e}")
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "Error checking username. Please try again."},
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
        cards = db.get_all_cards()
        return {"flashcards": cards}
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
@app.post("/donate/mpesa-stk")
async def donate_mpesa_stk(body: STKDonationRequest):
    try:
        # Validate required fields
        if not body.email or not body.phone or not body.amount:
            raise HTTPException(status_code=400, detail="Email, phone, and amount are required")
        
        if body.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        
        # Validate phone format
        if not re.match(r"^2547\d{8}$", body.phone):
            raise HTTPException(status_code=400, detail="Phone number must be in Safaricom MSISDN format: 254712345678")

        email_prefix = body.email.split("@")[0]
        api_ref = sanitize_api_ref(f"don-{email_prefix}-{int(body.amount*100)}")

        print(f"[DEBUG] Initiating M-Pesa STK push: amount={body.amount}, phone={body.phone}, email={body.email}")
        
        resp = service.collect.mpesa_stk_push(
            amount=body.amount,
            phone_number=body.phone.strip(),
            api_ref=api_ref,
            email=body.email,
            narrative=body.note or "Donation"
        )
        
        print(f"[DEBUG] IntaSend response: {resp}")
        
        data = getattr(resp, "data", {}) or getattr(resp, "__dict__", {}) or resp

        donation_id = (
            data.get("invoice_id")
            or data.get("id")
            or data.get("payment_id")
            or data.get("tracking_id")
            or (data.get("invoice", {}) or {}).get("invoice_id")
        )
        
        if not donation_id:
            print(f"[ERROR] IntaSend STK response missing donation ID fields: {data}")
            raise HTTPException(status_code=400, detail=f"IntaSend STK response missing donation ID fields: {data}")

        # TODO: Add donation record to DB if needed

        return {"status": "PENDING", "donation_id": donation_id, "message": "STK Push sent. Confirm on your phone."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] M-Pesa STK donation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment initiation failed: {str(e)}")

@app.post("/donate/checkout")
async def donate_checkout(body: CheckoutDonationRequest):
    try:
        # Validate required fields
        if not body.email or not body.amount:
            raise HTTPException(status_code=400, detail="Email and amount are required")
        
        if body.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")

        email_prefix = body.email.split("@")[0]
        api_ref = sanitize_api_ref(f"don-{email_prefix}-{body.currency.lower()}-{int(body.amount*100)}")

        print(f"[DEBUG] Initiating card checkout: amount={body.amount}, email={body.email}, currency={body.currency}")
        
        resp = service.collect.checkout(
            amount=body.amount,
            currency=body.currency,
            email=body.email,
            api_ref=api_ref,
            narrative="Donation"
        )
        
        print(f"[DEBUG] IntaSend checkout response: {resp}")
        
        data = getattr(resp, "data", {}) or getattr(resp, "__dict__", {}) or resp

        donation_id = (
            data.get("id")
            or data.get("invoice_id")
            or (data.get("invoice", {}) or {}).get("invoice_id")
        )
        checkout_url = data.get("url") or data.get("checkout_url")

        if not (donation_id and checkout_url):
            print(f"[ERROR] IntaSend checkout response missing fields: {data}")
            raise HTTPException(status_code=400, detail=f"IntaSend checkout response missing fields: {data}")

        # TODO: Add donation record to DB if needed

        return {"donation_id": donation_id, "checkout_url": checkout_url}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Card checkout donation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment initiation failed: {str(e)}")
    
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "QubitLearn Backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
