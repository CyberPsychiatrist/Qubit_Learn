from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional
from src.ai_processor import paraphrase_text, generate_questions
from FastAPI_backend.db import SupaDB
import os, pandas as pd, tempfile
from pathlib import Path

# --- Supabase setup ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
db = SupaDB(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter()

# ---------------- LOGIN ---------------- #
@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """Handles user login via HTML form."""
    user = db.login_user(email, password)
    if not user:
        return JSONResponse(
            {"error": "Invalid credentials or email not verified."},
            status_code=401
        )

    profile = db.get_user(user["id"])
    if not profile:
        return JSONResponse(
            {"error": "User profile not found after login."},
            status_code=404
        )

    # Save user session
    request.session["user"] = {
        "id": profile.get("id"),
        "email": email,
        "username": profile.get("username"),
        "full_name": profile.get("full_name")
    }

    # Redirect to dashboard after login
    return RedirectResponse(url="/dashboard", status_code=302)


# ---------------- SIGNUP ---------------- #
@router.post("/signup")
async def signup(
    email: str = Form(...),
    username: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...)
):
    """Handles user signup via HTML form."""
    try:
        # Check if user already exists
        existing_user = db.get_user(email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        # Create new user in Supabase Auth
        new_user = db.signup_user(email, password, full_name)
        if not new_user or not hasattr(new_user, "user"):
            raise HTTPException(status_code=500, detail="Error creating user in Supabase Auth")

        user_id = new_user.user.id
        db.save_user(user_id, email, username, full_name)

        return RedirectResponse(url="/login", status_code=302)

    except Exception as e:
        print(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Paraphrasing endpoint
@router.post("/api/paraphrase")
async def api_paraphrase(text: str = Form(...), num_return_sequences: int = Form(3)):
    result = paraphrase_text(text, num_return_sequences=num_return_sequences)
    return {"paraphrases": result}

# Question generation endpoint
@router.post("/api/questions")
async def api_questions(text: str = Form(...), max_questions: int = Form(5)):
    result = generate_questions(text, max_questions=max_questions)
    return {"questions": result}


# ---------------- FLASHCARDS ---------------- #
@router.get("/api/flashcards")
def get_flashcards(user_id: str):
    cards = db.get_user_flashcards(user_id)
    return {"flashcards": cards}


@router.post("/api/flashcards")
def add_flashcard(
    user_id: str = Form(...),
    question: str = Form(...),
    answer: str = Form(...)
):
    db.save_flashcards([{"question": question, "answer": answer}], user_id)
    return {"ok": True}


# ---------------- USER PROFILE ---------------- #
@router.get("/api/profile")
def get_profile(user_id: str):
    user = db.get_user_data(user_id)
    return {"profile": user}


@router.post("/api/profile")
def update_profile(user_id: str = Form(...), name: str = Form(...), email: str = Form(...)):
    result = db.update_user_profile(user_id, {"name": name, "email": email})
    return {"ok": True, "result": result}


# ---------------- STUDY TIMER ---------------- #
@router.get("/api/timer")
def get_timer(request: Request):
    return {"study_time": request.session.get("study_time", 0)}


@router.post("/api/timer")
def update_timer(request: Request, minutes: int = Form(...)):
    request.session["study_time"] = minutes
    return {"ok": True, "study_time": minutes}


# ---------------- FILE UPLOAD ---------------- #
@router.post("/api/upload")
async def upload_file(user_id: str = Form(...), file: UploadFile = File(...)):
    try:
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        if suffix == ".csv":
            df = pd.read_csv(tmp_path)
        elif suffix in [".xls", ".xlsx"]:
            df = pd.read_excel(tmp_path)
        elif suffix == ".json":
            df = pd.read_json(tmp_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        return {
            "ok": True,
            "filename": file.filename,
            "preview": df.head(5).to_dict(orient="records"),
            "summary": df.describe(include='all').to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
