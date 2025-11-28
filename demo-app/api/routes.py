"""
API routes for demo application
"""
from flask import jsonify, request
from models.user import User

def register_routes(app):
    @app.route('/api/users', methods=['GET'])
    def get_users():
        return jsonify({"users": [], "count": 0})
    
    @app.route('/api/users', methods=['POST'])
    def create_user():
        data = request.json
        user = User.create(
            name=data.get('name'),
            email=data.get('email')
        )
        return jsonify(user.to_dict()), 201
    
    @app.route('/api/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        return jsonify({"id": user_id, "message": "User not found"}), 404

