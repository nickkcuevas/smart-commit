"""
Configuration settings for demo app
"""
import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///demo.db')
    API_VERSION = '1.0.0'

