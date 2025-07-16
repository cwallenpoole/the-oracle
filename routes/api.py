"""
API routes for The Oracle application.
"""
import urllib.parse
import urllib.request
import json
import base64
import os
from datetime import datetime
from flask import Blueprint, request, current_app, jsonify, session
from logic.ai_readers import analyze_fire_image, generate_flame_reading
from models.user import User

api_bp = Blueprint('api', __name__)


@api_bp.route("/api/geocode")
def geocode():
    """Geocoding proxy to avoid CORS issues and hide implementation details"""
    address = request.args.get('address', '').strip()
    if not address:
        return {'error': 'Address parameter is required'}, 400

    try:
        # Use Nominatim (OpenStreetMap) geocoding service
        encoded_address = urllib.parse.quote(address)
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={encoded_address}&limit=1"

        # Add User-Agent header as required by Nominatim
        req = urllib.request.Request(url, headers={'User-Agent': 'Oracle-App/1.0'})

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

            if not data:
                return {'error': 'Location not found'}, 404

            result = data[0]
            return {
                'latitude': float(result['lat']),
                'longitude': float(result['lon']),
                'display_name': result['display_name'],
                'found': True
            }

    except Exception as e:
        current_app.logger.error(f"Geocoding error: {e}")
        return {'error': 'Geocoding service unavailable'}, 503


@api_bp.route("/api/save-fire-image", methods=['POST'])
def save_fire_image():
    """Save a captured fire animation image and optionally create a flame reading"""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400

        # Get the base64 image data
        image_data = data['image']

        # Remove the data URL prefix if present
        if image_data.startswith('data:image/png;base64,'):
            clean_image_data = image_data[22:]  # Remove "data:image/png;base64," prefix
        elif image_data.startswith('data:image/jpeg;base64,'):
            clean_image_data = image_data[23:]  # Remove "data:image/jpeg;base64," prefix
        else:
            clean_image_data = image_data

        # Decode the base64 image
        try:
            image_bytes = base64.b64decode(clean_image_data)
        except Exception as e:
            return jsonify({'error': 'Invalid image data format'}), 400

        # Create the fire captures directory if it doesn't exist
        captures_dir = os.path.join('static', 'fire-captures')
        os.makedirs(captures_dir, exist_ok=True)

        # Generate temporary filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        username = session.get('username', 'anonymous')
        temp_filename = f"fire_{username}_{timestamp}.png"
        temp_filepath = os.path.join(captures_dir, temp_filename)

        # Save the image with temporary filename
        with open(temp_filepath, 'wb') as f:
            f.write(image_bytes)

        # Get additional metadata if provided
        metadata = data.get('metadata', {})

        # Log the save event
        current_app.logger.info(f"Fire image saved: {temp_filepath} for user {username}")

        # Initialize response with temporary filename
        response_data = {
            'success': True,
            'filename': temp_filename,
            'path': temp_filepath,
            'timestamp': timestamp,
            'message': 'Fire image saved successfully'
        }

        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error(f"Error saving fire image: {e}")
        return jsonify({'error': 'Failed to save fire image'}), 500
