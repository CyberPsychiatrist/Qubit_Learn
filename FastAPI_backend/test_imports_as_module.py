#!/usr/bin/env python3
"""
Test script to verify imports work when running as a module
(simulating how FastAPI server would run)
"""

import sys
import os

# Add the current directory to Python path to simulate module import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports as they would be used in the FastAPI app"""
    try:
        # Test imports as they would be used when running the app
        print("Testing main.py imports...")
        from api import router as api_router
        from db import SupaDB
        print("✅ main.py imports successful")
        
        print("Testing api.py imports...")
        from ai_processor import paraphrase_text, generate_questions
        from db import SupaDB
        print("✅ api.py imports successful")
        
        print("Testing ai_processor.py imports...")
        # Test config import with fallback
        try:
            from config.settings import HUGGING_FACE_API_KEY as _HF_TOKEN_FROM_SETTINGS
        except ImportError:
            # Fallback to root level config if not found in current directory
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from config.settings import HUGGING_FACE_API_KEY as _HF_TOKEN_FROM_SETTINGS
        print("✅ ai_processor.py imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing FastAPI backend imports (as module)...")
    print("=" * 60)
    
    if test_imports():
        print("=" * 60)
        print("🎉 All imports working correctly!")
        print("The FastAPI backend should now deploy successfully to Render.")
    else:
        print("=" * 60)
        print("⚠️  Some imports failed. Check the errors above.")