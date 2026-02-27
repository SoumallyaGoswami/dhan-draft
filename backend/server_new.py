"""
New entry point for refactored application.

This replaces the monolithic server.py with the new modular architecture.
Run with: uvicorn server_new:app --host 0.0.0.0 --port 8001 --reload
"""
from app.main import app

# Export app for uvicorn
__all__ = ["app"]
