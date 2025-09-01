# tests/test_src_init.py
import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_src_imports():
    """Test that all modules in src can be imported"""
    try:
        import auth
        import ai_processor
        import flashcard_generator
        import utils
    except ImportError as e:
        pytest.fail(f"Failed to import src modules: {e}")

def test_src_module_contents():
    """Test that expected functions are available in src modules"""
    import auth
    import ai_processor
    import database
    
    # Test auth module
    assert hasattr(auth, 'login_user')
    assert hasattr(auth, 'init_supabase')
    
    assert hasattr(ai_processor, 'generate_questions')
    # Test flashcard_generator module
    
    assert hasattr(database, 'init_supabase')