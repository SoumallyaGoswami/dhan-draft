"""Utility functions for responses and helpers."""


def success_response(data=None, message="Success"):
    """Standard success response format."""
    return {
        "success": True,
        "data": data,
        "message": message
    }


def error_response(message="Error", data=None):
    """Standard error response format."""
    return {
        "success": False,
        "data": data,
        "message": message
    }
