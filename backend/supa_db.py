# backend/supa_db.py
from supabase import create_client, Client
from typing import Optional, List, Dict, Any


class SupaDB:
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)

    # ----- Donations -----
    def add_donation(
        self,
        donation_id: str,
        email: str,
        amount: float,
        currency: str,
        method: str,
        status: str,
        api_ref: str,
    ) -> Dict[str, Any]:
        payload = {
            "id": donation_id,
            "email": email,
            "amount": amount,
            "currency": currency,
            "method": method,
            "status": status,
            "api_ref": api_ref,
        }
        res = self.client.table("donations").insert(payload).execute()
        if hasattr(res, "error") and res.error:
            raise RuntimeError(f"❌ Supabase insert error: {res.error}")
        return {"data": res.data}

    def update_donation_status(
        self, donation_id: str, status: str, currency: Optional[str] = None
    ) -> None:
        update = {"status": status}
        if currency:
            update["currency"] = currency

        res = (
            self.client.table("donations")
            .update(update)
            .eq("id", donation_id)
            .execute()
        )
        if hasattr(res, "error") and res.error:
            raise RuntimeError(f"❌ Supabase update error: {res.error}")

    def get_donation_by_id(self, donation_id: str) -> Optional[Dict[str, Any]]:
        res = (
            self.client.table("donations")
            .select("*")
            .eq("id", donation_id)
            .single()
            .execute()
        )
        if hasattr(res, "error") and res.error:
            raise RuntimeError(f"❌ Supabase fetch error: {res.error}")
        return res.data if res and res.data else None

    def get_donations(self, email: str) -> List[Dict[str, Any]]:
        res = (
            self.client.table("donations")
            .select("*")
            .eq("email", email)
            .order("created_at", desc=True)
            .execute()
        )
        if hasattr(res, "error") and res.error:
            raise RuntimeError(f"❌ Supabase fetch error: {res.error}")
        return res.data or []
