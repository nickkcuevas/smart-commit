"""
User model for demo application
"""
from datetime import datetime

class User:
    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email
        self.created_at = datetime.now()
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def create(cls, name: str, email: str):
        # Simulate database ID
        user_id = hash(email) % 10000
        return cls(user_id, name, email)

