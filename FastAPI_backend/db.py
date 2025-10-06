from supabase import create_client, Client
from typing import Optional, List, Dict, Any
import uuid


class SupaDB:
    # -------------------- FLASHCARDS -------------------- #
    def insert_cards(self, rows: List[Dict[str, Any]]):
        """
        Insert rows into public.cards. Each row: {"question": str, "answer": str, ["created_by": uuid]}
        Returns (success: bool, data or error message)
        """
        rows = [r for r in rows if r.get("question") and r.get("answer")]
        if not rows:
            return False, "No valid rows to insert."
        try:
            res = self.client.table("cards").insert(rows).execute()
            if getattr(res, "error", None):
                err_txt = str(res.error)
                # Retry without created_by if column missing
                if "created_by" in str(rows) and ("42703" in err_txt or "created_by" in err_txt and "column" in err_txt.lower()):
                    rows_wo = [{k: v for k, v in row.items() if k != "created_by"} for row in rows]
                    res2 = self.client.table("cards").insert(rows_wo).execute()
                    if getattr(res2, "error", None):
                        return False, str(res2.error)
                    return True, getattr(res2, "data", None)
                return False, err_txt
            return True, getattr(res, "data", None)
        except Exception as e:
            return False, f"Insert error: {e}"
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)

    # -------------------- AUTH -------------------- #
    def signup_user(self, email: str, password: str, full_name: str):
        """Register a new user using Supabase Auth."""
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {"full_name": full_name}
                }
            })

            if not response or not getattr(response, "user", None):
                raise Exception("Signup failed or email already registered.")

            print(f"✅ User signed up: {response.user.email}")
            return response

        except Exception as e:
            print(f"❌ Error during signup: {e}")
            raise Exception(f"Signup failed: {e}")

    def login_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user via Supabase Auth and return profile info."""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if response and getattr(response, "user", None):
                print(f"✅ User logged in: {response.user.email}")
                return {
                    "id": response.user.id,
                    "email": response.user.email,
                    "full_name": response.user.user_metadata.get("full_name", "")
                }

            print(f"⚠️ Invalid login attempt for {email}")
            return None

        except Exception as e:
            print(f"❌ Error during login: {e}")
            raise Exception(f"Login failed: {e}")

    def resend_confirmation(self, email: str):
        """Resend email confirmation link."""
        try:
            return self.client.auth.resend({
                "email": email,
                "type": "signup"
            })
        except Exception as e:
            print(f"❌ Error resending confirmation: {e}")
            raise Exception(f"Resend confirmation failed: {e}")

    # -------------------- USERS -------------------- #
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Fetch a user record from 'users' table by email."""
        try:
            response = self.client.table("users").select("*").eq("email", email).limit(1).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"❌ Error fetching user by email: {e}")
            raise Exception(f"Failed to get user by email: {e}")

    def save_user(self, user_id: str, email: str, username: str, full_name: str):
        """Insert user into 'users' table if not already present."""
        try:
            existing = self.client.table("users").select("id").eq("id", user_id).execute()

            if not existing.data:
                print(f"🆕 Inserting new user record for {email}")
                self.client.table("users").insert({
                    "id": user_id,
                    "email": email,
                    "username": username,
                    "full_name": full_name
                }).execute()
            else:
                print(f"✅ User {email} already exists in 'users' table.")
        except Exception as e:
            print(f"❌ Error saving user: {e}")
            raise Exception(f"Failed to save user: {e}")

    def get_user(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Fetch a user record by either email or UUID."""
        try:
            try:
                uuid.UUID(str(identifier))
                field = "id"
            except ValueError:
                field = "email"

            response = self.client.table("users").select("*").eq(field, identifier).limit(1).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"❌ Error fetching user: {e}")
            raise Exception(f"Failed to get user: {e}")

    # -------------------- DONATIONS -------------------- #
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
        """Insert a donation record into 'donations' table."""
        try:
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
            print(f"💰 Donation recorded for {email}")
            return {"data": res.data}
        except Exception as e:
            print(f"❌ Error adding donation: {e}")
            raise Exception(f"Failed to add donation: {e}")

    def update_donation_status(self, donation_id: str, status: str, currency: Optional[str] = None):
        """Update donation status in 'donations' table."""
        try:
            update = {"status": status}
            if currency:
                update["currency"] = currency
            self.client.table("donations").update(update).eq("id", donation_id).execute()
            print(f"✅ Donation {donation_id} updated to {status}")
        except Exception as e:
            print(f"❌ Error updating donation: {e}")
            raise Exception(f"Failed to update donation: {e}")

    def get_donation_by_id(self, donation_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a donation record by ID."""
        try:
            res = self.client.table("donations").select("*").eq("id", donation_id).limit(1).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            print(f"❌ Error fetching donation: {e}")
            raise Exception(f"Failed to get donation by ID: {e}")

    def get_donations(self, email: str) -> List[Dict[str, Any]]:
        """Get all donations for a given user by email."""
        try:
            res = (
                self.client.table("donations")
                .select("*")
                .eq("email", email)
                .order("created_at", desc=True)
                .execute()
            )
            return res.data or []
        except Exception as e:
            print(f"❌ Error fetching donations: {e}")
            raise Exception(f"Failed to get donations: {e}")
