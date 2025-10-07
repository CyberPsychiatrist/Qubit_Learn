#!/usr/bin/env python3
"""
Test script to verify all imports are working correctly
"""

def test_main_imports():
    """Test imports from main.py"""
    try:
        from .api import router as api_router
        from .db import SupaDB
        print("✅ main.py imports successful")
        return True
    except ImportError as e:
        print(f"❌ main.py import failed: {e}")
        return False

def test_api_imports():
    """Test imports from api.py"""
    try:
        from .ai_processor import paraphrase_text, generate_questions
        from .db import SupaDB
        print("✅ api.py imports successful")
        return True
    except ImportError as e:
        print(f"❌ api.py import failed: {e}")
        return False

def test_ai_processor_imports():
    """Test imports from ai_processor.py"""
    try:
        # Test config import with fallback
        try:
            from .config.settings import HUGGING_FACE_API_KEY as _HF_TOKEN_FROM_SETTINGS
        except ImportError:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from config.settings import HUGGING_FACE_API_KEY as _HF_TOKEN_FROM_SETTINGS
        
        print("✅ ai_processor.py imports successful")
        return True
    except ImportError as e:
        print(f"❌ ai_processor.py import failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing FastAPI backend imports...")
    print("=" * 50)
    
    success = True
    success &= test_main_imports()
    success &= test_api_imports()
    success &= test_ai_processor_imports()
    
    print("=" * 50)
    if success:
        print("🎉 All imports working correctly!")
    else:
        print("⚠️  Some imports failed. Check the errors above.")