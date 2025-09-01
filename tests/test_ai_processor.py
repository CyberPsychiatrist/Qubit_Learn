import pytest
from unittest.mock import patch, MagicMock
import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def sample_text():
    return "Sample content for question generation."

@patch('src.ai_processor.requests.post')
def test_generate_questions_success(mock_post, sample_text):
    """Test successful question generation"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "question": "Who created Python?",
        "answer": "Guido van Rossum"
    }
    mock_post.return_value = mock_response
    
    # Import after patching
    from src.ai_processor import generate_questions
    
    # Execute function
    questions = generate_questions(sample_text, num_questions=2)
    
    assert len(questions) == 2
    assert questions[1] == {"question": "Who created Python?", "answer": "Guido van Rossum"}
    assert mock_post.call_count == 2

@patch('src.ai_processor.requests.post')
def test_generate_questions_api_error(mock_post, sample_text):
    """Test question generation when API returns error"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {}
    mock_post.return_value = mock_response
    
    # Import after patching
    from src.ai_processor import generate_questions
    
    # Execute function
    questions = generate_questions(sample_text, num_questions=1)
    
    # Assertions
    assert len(questions) == 0
    assert mock_post.call_count == 1

@patch('src.ai_processor.requests.post')
@patch('src.ai_processor.HUGGING_FACE_API_KEY', 'test_api_key')
def test_generate_questions_network_error(mock_post, mock_api_key, sample_text):
    """Test question generation when network error occurs"""
    mock_post.side_effect = requests.exceptions.RequestException("Network error")
    
    from src.ai_processor import generate_questions
    
    # Execute function
    questions = generate_questions(sample_text, num_questions=1)
    
    # Assertions
    assert mock_post.call_count == 1
    assert len(questions) == 0

@patch('src.ai_processor.HUGGING_FACE_API_KEY', 'test_api_key')
def test_generate_questions_with_empty_text(mock_post):
    """Test question generation with empty text"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "question": "What is this?",
        "answer": "Empty text"
    }
    mock_post.return_value = mock_response
    
    from src.ai_processor import generate_questions
    
    # Execute function
    questions = generate_questions("", num_questions=1)
    
    # Assertions
    assert mock_post.call_count == 1

@patch('src.ai_processor.HUGGING_FACE_API_KEY', 'test_api_key')
def test_generate_questions_truncates_long_text(mock_post):
    """Test that long text is truncated"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "question": "What is this?",
        "answer": "Truncated text"
    }
    mock_post.return_value = mock_response
    
    from src.ai_processor import generate_questions
    
    # Create long text (more than 1000 characters)
    long_text = "a" * 1500
    # Execute function
    questions = generate_questions(long_text, num_questions=1)
    
    # Assertions
    assert len(questions) == 1
    mock_post.assert_called_once()
