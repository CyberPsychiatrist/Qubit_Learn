from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY


# Initialize Supabase client
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_user_flashcards(user_id: str):
    """Fetch the user's flashcards from the database."""
    try:
        supabase_client = init_supabase()
        response = (
            supabase_client.table("cards")
            .select("*")
            .eq("created_by", user_id)
            .execute()
        )
        return response.data or []
    except Exception as e:
        return {"error": str(e)}


def save_flashcards(cards: list, user_id: str, source: str = "original"):
    """Save flashcards to the database, with source (original/paraphrased)."""
    supabase_client = init_supabase()
    results = []

    for card in cards:
        try:
            card_data = {
                "question": card.get("question"),
                "answer": card.get("answer"),
                "created_by": user_id,
                "source": source,
            }
            response = supabase_client.table("cards").insert(card_data).execute()
            results.append(response.data)
        except Exception as e:
            results.append({"error": str(e)})

    return results


def get_user_data(user_id: str):
    """Fetch a user's profile data from the database."""
    try:
        supabase_client = init_supabase()
        response = (
            supabase_client.table("users")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        return {"error": str(e)}


def update_user_profile(user_id: str, profile_data: dict):
    """Update a user's profile in the database."""
    try:
        supabase_client = init_supabase()
        response = (
            supabase_client.table("users")
            .update(profile_data)
            .eq("id", user_id)
            .execute()
        )
        return response.data
    except Exception as e:
        return {"error": str(e)}
