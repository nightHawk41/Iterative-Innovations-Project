"""
conftest.py — place this file at backend/tests/conftest.py
 
Adds the backend root to sys.path so `from app import ...` works
without needing to install the package.
"""
 
import sys
import os
 
# backend/ is two levels up from backend/app/tests/conftest.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
 