import pytest
from src.flashcard_generator import create_flashcards

def test_create_flashcards_with_valid_input():
    """Test flashcard creation with valid question data"""
    questions = [
        {"question": "What is Python?", "answer": "A programming language"},
        {"question": "What is Streamlit?", "answer": "A Python web framework"}
    ]
    
    flashcards = create_flashcards(questions)
    
    assert len(flashcards) == 2
    assert flashcards[0]["id"] == 0
    assert flashcards[0]["question"] == "What is Python?"
    assert flashcards[0]["answer"] == "A programming language"
    assert flashcards[1]["id"] == 1
    assert flashcards[1]["question"] == "What is Streamlit?"
    assert flashcards[1]["answer"] == "A Python web framework"

def test_create_flashcards_with_empty_input():
    """Test flashcard creation with empty input"""
    questions = []
    flashcards = create_flashcards(questions)
    assert flashcards == {"error": "Input list cannot be empty"}

def test_create_flashcards_with_missing_keys():
    """Test flashcard creation when questions have missing keys"""
    questions = [
        {"question": "What is Python?"},
        {"answer": "A programming language"},
        {}
    ]
    
    flashcards = create_flashcards(questions)
    
    assert len(flashcards) == 3
    assert flashcards[0]["question"] == "What is Python?"
    assert flashcards[0]["answer"] == "No answer generated"
    assert flashcards[1]["question"] == "No question generated"
    assert flashcards[1]["answer"] == "A programming language"
    assert flashcards[2]["question"] == "No question generated"
    assert flashcards[2]["answer"] == "No answer generated"

def test_create_flashcards_non_list_input():
    """Test flashcard creation with non-list input"""
    # Test with string input
    result = create_flashcards("not a list")
    assert result["error"] == "Input must be a list of questions"
    
    # Test with integer input
    result = create_flashcards(123)
    assert result["error"] == "Input must be a list of questions"
