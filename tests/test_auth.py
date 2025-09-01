# tests/test_auth.py
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_login_user():
    """Test login functionality"""
    with patch('src.auth.supabase.create_client') as mock_create_client:
        mock_client = MagicMock()
        mock_auth = MagicMock()
        mock_response = MagicMock()
        
        mock_auth.sign_in_with_password.return_value = mock_response
        mock_client.auth = mock_auth
        mock_create_client.return_value = mock_client
        
        # Import after patching
        from src.auth import login_user
        result = login_user("test@example.com", "password123")
        
        assert result == mock_response
        mock_auth.sign_in_with_password.assert_called_once_with({
            "email": "test@example.com",
            "password": "password123"
        })

def test_login_user_exception():
    """Test login functionality when exception occurs"""
    with patch('src.auth.supabase.create_client') as mock_create_client:
        mock_auth = MagicMock()
        mock_client = MagicMock()
        mock_client.auth = mock_auth
        mock_auth.sign_in_with_password.side_effect = Exception("Auth error")
        mock_create_client.return_value = mock_client
        
        # Import after patching
        from src.auth import login_user
        result = login_user("test@example.com", "password123")
        
        assert result is None

def test_register_user():
    """Test registration functionality"""
    with patch('src.auth.supabase.create_client') as mock_create_client:
        mock_client = MagicMock()
        mock_auth = MagicMock()
        
        mock_response = MagicMock()
        mock_client.auth = mock_auth
        mock_auth.sign_up.return_value = mock_response
        
        mock_create_client.return_value = mock_client
        # Import after patching
        from src.auth import register_user
        result = register_user("test@example.com", "password123")
        
        assert result == mock_response
        mock_auth.sign_up.assert_called_once_with({
            "email": "test@example.com",
            "password": "password123"
        })

def test_register_user_exception():
    """Test registration functionality when exception occurs"""
    with patch('src.auth.supabase.create_client') as mock_create_client:
        mock_client = MagicMock()
        mock_auth = MagicMock()
        mock_client.auth = mock_auth
        mock_auth.sign_up.side_effect = Exception("Registration error")
        mock_create_client.return_value = mock_client
        
        # Import after patching
        from src.auth import register_user
        result = register_user("test@example.com", "password123")
        
        assert result is None
def test_login_user_invalid_email():
    """Test login with invalid email format"""
    with patch('src.auth.supabase.create_client') as mock_create_client:
        mock_client = MagicMock()
        mock_auth = MagicMock()
        mock_create_client.return_value = mock_client
        
        # Import after patching
        from src.auth import login_user
        result = login_user("testexample.com", "password123")
        
        assert result["error"] == "Invalid email format"
        mock_auth.sign_in_with_password.assert_not_called()

def test_register_user_invalid_email():
    """Test registration with invalid email format"""
    with patch('src.auth.supabase.create_client') as mock_create_client:
        mock_client = MagicMock()
        mock_auth = MagicMock()
        mock_create_client.return_value = mock_client
        
        # Import after patching
        from src.auth import register_user
        result = register_user("testexample.com", "password123")
        
        assert result["error"] == "Invalid email format"
        mock_auth.sign_up.assert_not_called()