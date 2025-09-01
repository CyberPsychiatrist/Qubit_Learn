# backend/backend.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from dotenv import load_dotenv
from intasend import APIService
import os
import re

# --- Load env for backend only ---
load_dotenv()

# IntaSend creds
INTASEND_SECRET_TOKEN = os.getenv("INTASEND_SECRET_TOKEN")
INTASEND_PUBLISHABLE_KEY = os.getenv("INTASEND_PUBLISHABLE_KEY")
TEST_MODE = os.getenv("INTASEND_TEST_MODE", "true").lower() in ("1", "true", "yes")

if not INTASEND_SECRET_TOKEN or not INTASEND_PUBLISHABLE_KEY:
    raise RuntimeError("❌ Missing INTASEND_SECRET_TOKEN or INTASEND_PUBLISHABLE_KEY in environment.")

# Supabase creds
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Prefer service role key on backend
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

# Allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------- Helper -----------
def sanitize_api_ref(text: str) -> str:
    """Replace disallowed characters with '-' (IntaSend only allows letters, numbers, _, -, space)."""
    return re.sub(r"[^a-zA-Z0-9_\- ]", "-", text)

# ----------- Schemas -----------
class STKDonationRequest(BaseModel):
    email: EmailStr
    phone: str = Field(..., description="MSISDN format, e.g. 2547XXXXXXXX")
    amount: float = Field(gt=0)
    note: Optional[str] = None
    currency: str = "KES"  # STK is KES only

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
    try:
        api_ref = sanitize_api_ref(f"don-{body.email}-kes-{int(body.amount*100)}")

        resp = service.collect.mpesa_stk_push(
            amount=body.amount,
            phone_number=body.phone,
            api_ref=api_ref,
            email=body.email,
            narrative=body.note or "Donation"
        )

        data = getattr(resp, "data", {}) or getattr(resp, "__dict__", {}) or resp
        print("🔍 Full IntaSend STK Response:", data)

        donation_id = (
            data.get("invoice_id")
            or data.get("id")
            or data.get("payment_id")
            or data.get("tracking_id")
            or (data.get("invoice", {}) or {}).get("invoice_id")
        )

        if not donation_id:
            raise HTTPException(status_code=400, detail=f"IntaSend STK response missing donation ID fields: {data}")

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
    try:
        api_ref = sanitize_api_ref(f"don-{body.email}-{body.currency.lower()}-{int(body.amount*100)}")

        resp = service.collect.checkout(
            amount=body.amount,
            currency=body.currency,
            email=body.email,
            api_ref=api_ref,
            narrative="Donation"
        )

        data = getattr(resp, "data", {}) or getattr(resp, "__dict__", {}) or resp
        print("🔍 Full IntaSend Checkout Response:", data)

        donation_id = (
            data.get("id")
            or data.get("invoice_id")
            or (data.get("invoice", {}) or {}).get("invoice_id")
        )
        checkout_url = data.get("url") or data.get("checkout_url")

        if not (donation_id and checkout_url):
            raise HTTPException(status_code=400, detail=f"IntaSend checkout response missing fields: {data}")

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
    payload = await request.json()
    donation_id = payload.get("id") or payload.get("invoice_id")
    status = payload.get("status")
    currency = payload.get("currency")
    email = payload.get("email") or payload.get("customer_email")

    if donation_id and status:
        db.update_donation_status(donation_id, status, currency=currency)
        print(f"🔔 Webhook: {donation_id} | {email} | {currency} | {status}")

    return {"ok": True}
