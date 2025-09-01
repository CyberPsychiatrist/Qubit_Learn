import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client"""
    with patch('src.database.supabase.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance

def test_init_supabase(mock_supabase_client):
    """Test Supabase client initialization"""
    from src.database import init_supabase
    client = init_supabase()
    mock_supabase_client.assert_called_once_with('test_url', 'test_key')

@patch('src.database.init_supabase')
def test_save_flashcards(mock_init_supabase):
    """Test saving flashcards to database"""
    mock_client = MagicMock()
    mock_init_supabase.return_value = mock_client
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    
    flashcards = [
        {"question": "What is Python?", "answer": "A programming language"},
        {"question": "What is Streamlit?", "answer": "A Python web framework"}
    ]
    user_id = "test_user_id"
    
    from src.database import save_flashcards
    
    save_flashcards(flashcards, user_id)
    
    assert mock_client.table.call_count == 2
    assert mock_table.insert.call_count == 2
    mock_table.insert.assert_any_call({
        "question": "What is Python?",
        "answer": "A programming language",
        "created_by": user_id
    })
    mock_table.insert.assert_any_call({
        "question": "What is Streamlit?",
        "answer": "A Python web framework",
        "created_by": user_id
    })

@patch('src.database.init_supabase')
def test_get_user_flashcards(mock_init_supabase):
    """Test retrieving user flashcards"""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_execute = MagicMock()
    mock_table.eq.return_value = mock_table
    mock_execute.data = [
        {"id": 1, "question": "Test Q1", "answer": "Test A1", "created_by": "user1"},
        {"id": 2, "question": "Test Q2", "answer": "Test A2", "created_by": "user1"}
    ]
    mock_table.execute.return_value = mock_execute
    
    from src.database import get_user_flashcards
    
    result = get_user_flashcards("user1")
    mock_table.select.assert_called_with("*")
    mock_table.eq.assert_called_with("created_by", "user1")
    mock_table.execute.assert_called_once()
    assert len(result) == 2
    assert result[0]["question"] == "Test Q1"
    assert result[1]["answer"] == "Test A2"
