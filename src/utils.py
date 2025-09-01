

def validate_email(email):
    """Enhanced email validation with regex pattern"""
    import re
    if '@' not in email or '.' not in email.split('@')[1]:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def truncate_text(text, max_length=100):
    """Truncate text to a maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def format_flashcard_count(count):
    """Format flashcard count for display"""
    if count == 1:
        return "1 flashcard"
    return f"{count} flashcards"
