"""
Refactored entry point - imports from modular architecture.

This file replaces the monolithic 982-line server.py with a clean import
from the new modular structure in app/.

Original monolithic file backed up as server_old.py
"""
from app.main import app

# Export app for uvicorn (supervisor uses: uvicorn server:app)
__all__ = ["app"]
