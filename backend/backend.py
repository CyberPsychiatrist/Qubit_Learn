# backend/backend.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from dotenv import load_dotenv
from intasend import APIService
import os

# --- Load env for backend only ---
load_dotenv()

# IntaSend creds (SECRET must be here on the backend only)
INTASEND_SECRET_TOKEN = os.getenv("INTASEND_SECRET_TOKEN")
INTASEND_PUBLISHABLE_KEY = os.getenv("INTASEND_PUBLISHABLE_KEY")
TEST_MODE = os.getenv("INTASEND_TEST_MODE", "true").lower() in ("1", "true", "yes")

if not INTASEND_SECRET_TOKEN or not INTASEND_PUBLISHABLE_KEY:
    raise RuntimeError("❌ Missing INTASEND_SECRET_TOKEN or INTASEND_PUBLISHABLE_KEY in environment.")

# Supabase creds (backend uses service role or anon with RLS = off for this table)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Prefer a Service Role key on backend
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("❌ Missing SUPABASE_URL or SUPABASE_KEY in environment.")

# --- Init IntaSend SDK ---
service = APIService(
    token=INTASEND_SECRET_TOKEN,
    publishable_key=INTASEND_PUBLISHABLE_KEY,
    test=TEST_MODE,
)

# --- DB layer using Supabase ---
from .supa_db import SupaDB
db = SupaDB(SUPABASE_URL, SUPABASE_KEY)

# --- FastAPI app ---
app = FastAPI(title="Donate API (IntaSend x Supabase)")

# Allow the Streamlit app to call us; tighten CORS in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace with your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------- Schemas -----------
class STKDonationRequest(BaseModel):
    email: EmailStr
    phone: str = Field(..., description="MSISDN format, e.g. 2547XXXXXXXX")
    amount: float = Field(gt=0)
    note: Optional[str] = None
    currency: str = "KES"  # STK is KES

class CheckoutDonationRequest(BaseModel):
    email: EmailStr
    amount: float = Field(gt=0)
    currency: str = Field(default="USD", description="USD or KES")


# ----------- Routes -----------
@app.get("/health")
def health():
    return {"ok": True, "intasend_test_mode": TEST_MODE}

@app.post("/donate/mpesa-stk")
def donate_mpesa_stk(body: STKDonationRequest):
    """
    Create an M-Pesa STK push. Saves a PENDING donation row in Supabase.
    Webhook will flip status to COMPLETED/FAILED.
    """
    try:
        api_ref = f"don-{body.email}-kes-{int(body.amount*100)}"
        resp = service.collect.mpesa_stk_push(
            amount=body.amount,
            phone_number=body.phone,
            api_ref=api_ref,
            email=body.email,
            narrative=body.note or "Donation"
        )
        data = getattr(resp, "data", {}) or {}
        donation_id = data.get("invoice_id") or data.get("id")
        if not donation_id:
            raise HTTPException(status_code=400, detail=f"IntaSend response missing invoice_id: {data}")

        # Save in Supabase
        db.add_donation(
            donation_id=donation_id,
            email=body.email,
            amount=body.amount,
            currency=body.currency,
            method="MPESA_STK",
            status="PENDING",
            api_ref=api_ref,
        )
        return {"ok": True, "donation_id": donation_id, "message": "📲 STK Push sent. Confirm on your phone."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/donate/checkout")
def donate_checkout(body: CheckoutDonationRequest):
    """
    Create a hosted checkout (Card/PayPal).
    """
    try:
        api_ref = f"don-{body.email}-{body.currency.lower()}-{int(body.amount*100)}"
        resp = service.checkout.create(
            amount=body.amount,
            currency=body.currency,
            email=body.email,
            api_ref=api_ref,
            description="Donation"
        )
        data = getattr(resp, "data", {}) or {}
        donation_id = data.get("id") or data.get("invoice_id")
        checkout_url = data.get("url") or data.get("checkout_url")
        if not (donation_id and checkout_url):
            raise HTTPException(status_code=400, detail=f"IntaSend checkout response unexpected: {data}")

        db.add_donation(
            donation_id=donation_id,
            email=body.email,
            amount=body.amount,
            currency=body.currency,
            method="CHECKOUT",
            status="PENDING",
            api_ref=api_ref,
        )
        return {"ok": True, "donation_id": donation_id, "checkout_url": checkout_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/donations/{donation_id}")
def donation_status(donation_id: str):
    """
    Fetch donation status from Supabase (webhook is source of truth).
    """
    row = db.get_donation_by_id(donation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Donation not found")
    return {"ok": True, "donation": row}

@app.get("/donations")
def donations_by_email(email: EmailStr):
    rows = db.get_donations(email)
    return {"ok": True, "donations": rows}

@app.post("/webhook/intasend")
async def intasend_webhook(request: Request):
    """
    Configure this URL in IntaSend dashboard as your webhook.
    If you're running locally, expose with ngrok and use that URL.
    """
    payload = await request.json()

    # Optional but recommended:
    # event = service.webhooks.validate(payload)  # validates signature/HMAC if configured
    # We'll proceed directly, but you should enable validation once set.

    # Expected fields vary by event type; we handle common ones:
    donation_id = payload.get("id") or payload.get("invoice_id")
    status = payload.get("status")
    currency = payload.get("currency")
    email = payload.get("email") or payload.get("customer_email")

    if donation_id and status:
        db.update_donation_status(donation_id, status, currency=currency)
        print(f"🔔 Webhook: {donation_id} | {email} | {currency} | {status}")

    return {"ok": True}
