"""
Demo application for Smart Commit demonstration
"""
from flask import Flask, jsonify, request
from models.user import User
from api.routes import register_routes

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"message": "Welcome to Demo App", "version": "1.0.0"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

register_routes(app)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

