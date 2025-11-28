"""
Tests for API endpoints
"""
import unittest
from app import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
    
    def test_index(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_health(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertIn("status", response.json)

