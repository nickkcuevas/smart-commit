"""
Tests for User model
"""
import unittest
from models.user import User

class TestUser(unittest.TestCase):
    def test_user_creation(self):
        user = User(1, "John Doe", "john@example.com")
        self.assertEqual(user.name, "John Doe")
        self.assertEqual(user.email, "john@example.com")
    
    def test_user_to_dict(self):
        user = User(1, "Jane Doe", "jane@example.com")
        user_dict = user.to_dict()
        self.assertIn("id", user_dict)
        self.assertIn("name", user_dict)
        self.assertIn("email", user_dict)

