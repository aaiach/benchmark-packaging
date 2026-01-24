from flask import Blueprint, request, jsonify
from api.src.services.email_service import validate_and_store_email

email_bp = Blueprint('email', __name__)

@email_bp.route('/validate', methods=['POST'])
def validate_email_route():
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400
    
    result = validate_and_store_email(data['email'])
    
    if not result['valid']:
        return jsonify(result), 400
        
    return jsonify(result)
