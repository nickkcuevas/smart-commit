"""
Helper utility functions
"""
import re

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def format_name(name: str) -> str:
    """Format name with proper capitalization"""
    return name.strip().title()

def generate_user_id(email: str) -> int:
    """Generate a user ID from email"""
    return abs(hash(email)) % 100000

