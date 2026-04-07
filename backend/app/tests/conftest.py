# """
# conftest.py — place this file at backend/tests/conftest.py
 
# Adds the backend root to sys.path so `from app import ...` works
# without needing to install the package.
# """
 
# import sys
# import os
 
# # backend/ is two levels up from backend/app/tests/conftest.py
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

"""
conftest.py
Configures Pytest fixtures for the entire testing suite.
"""

import sys
import os
import pytest

# backend/ is two levels up from backend/app/tests/conftest.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from flask import Flask
from app import db

# Import models so SQLAlchemy registers them before create_all()
from app.models.item_slot import ItemSlot
from app.models.transaction import Transaction
from app.models.notification import Notification

@pytest.fixture
def app():
    """
    Creates a fresh Flask application and a completely clean 
    in-memory SQLite database for every test.
    """
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"   # Isolated, in-memory DB
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True

    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app  # This hands the app over to the test!
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A mock client for routing API requests in tests."""
    return app.test_client()
 