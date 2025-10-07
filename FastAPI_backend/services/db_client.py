# services/db_client.py
from __future__ import annotations
import os
from typing import List, Dict, Any, Optional, Tuple

import requests

# Try to use supabase client if available (preferred)
try:
    from supabase import create_client, Client  # type: ignore
except Exception:
    create_client = None
    Client = None  # type: ignore


def _get_env(name: str) -> Optional[str]:
    val = os.getenv(name)
    if val:
        return val
    # Try Streamlit secrets lazily (avoid hard dependency)
    try:
        import streamlit as st  # type: ignore
        return st.secrets.get(name)  # type: ignore[attr-defined]
    except Exception:
        return None


def _get_supabase_client() -> Optional["Client"]:
    if create_client is None:
        return None
    url = _get_env("SUPABASE_URL")
    key = _get_env("SUPABASE_ANON_KEY") or _get_env("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


def _postgrest_insert(rows: List[Dict[str, Any]]) -> Tuple[bool, Any]:
    """
    Fallback path: call PostgREST directly.
    Requires SUPABASE_URL + SUPABASE_ANON_KEY (or service key).
    """
    base = _get_env("SUPABASE_URL")
    key = _get_env("SUPABASE_ANON_KEY") or _get_env("SUPABASE_SERVICE_ROLE_KEY")
    if not base or not key:
        return False, "Missing SUPABASE_URL or key for PostgREST."

    rest_url = base.rstrip("/") + "/rest/v1/cards"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    try:
        r = requests.post(rest_url, headers=headers, json=rows, timeout=45)
        if r.status_code >= 400:
            # If created_by is unknown column, try again without it
            txt = r.text.lower()
            if "created_by" in str(rows) and ("42703" in txt or "column" in txt and "created_by" in txt):
                rows_wo = [{k: v for k, v in row.items() if k != "created_by"} for row in rows]
                r2 = requests.post(rest_url, headers=headers, json=rows_wo, timeout=45)
                if r2.status_code >= 400:
                    return False, r2.text
                return True, r2.json()
            return False, r.text
        return True, r.json()
    except Exception as e:
        return False, f"PostgREST error: {e}"


def insert_cards(rows: List[Dict[str, Any]]) -> Tuple[bool, Any]:
    """
    Insert rows into public.cards. Each row: {"question": str, "answer": str, ["created_by": uuid]}
    Tries Supabase client first; falls back to PostgREST.
    """
    rows = [r for r in rows if r.get("question") and r.get("answer")]
    if not rows:
        return False, "No valid rows to insert."

    sb = _get_supabase_client()
    if sb is not None:
        try:
            res = sb.table("cards").insert(rows).execute()
            # supabase-py v2 returns data in res.data and error in res.error
            if getattr(res, "error", None):
                err_txt = str(res.error)
                # Retry without created_by if column missing
                if "created_by" in str(rows) and ("42703" in err_txt or "created_by" in err_txt and "column" in err_txt.lower()):
                    rows_wo = [{k: v for k, v in row.items() if k != "created_by"} for row in rows]
                    res2 = sb.table("cards").insert(rows_wo).execute()
                    if getattr(res2, "error", None):
                        return False, str(res2.error)
                    return True, getattr(res2, "data", None)
                return False, err_txt
            return True, getattr(res, "data", None)
        except Exception as e:
            # fall through to PostgREST
            pass

    return _postgrest_insert(rows)


def current_user_id_from_session() -> Optional[str]:
    """
    Attempts to discover a user id from Streamlit session state.
    Accepts common keys: id, user_id, uuid, sub.
    """
    try:
        import streamlit as st  # type: ignore
        user = st.session_state.get("user") or {}
        for key in ("id", "user_id", "uuid", "sub"):
            if user.get(key):
                return str(user[key])
    except Exception:
        return None
    return None
