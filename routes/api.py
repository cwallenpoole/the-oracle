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

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        username = session.get('username', 'anonymous')
        filename = f"fire_{username}_{timestamp}.png"
        filepath = os.path.join(captures_dir, filename)

        # Save the image
        with open(filepath, 'wb') as f:
            f.write(image_bytes)

        # Get additional metadata if provided
        metadata = data.get('metadata', {})

        # Log the save event
        current_app.logger.info(f"Fire image saved: {filepath} for user {username}")

        # Initialize response
        response_data = {
            'success': True,
            'filename': filename,
            'path': filepath,
            'timestamp': timestamp,
            'message': 'Fire image saved successfully'
        }

        # If user is logged in, perform vision analysis and create flame reading
        if username != 'anonymous' and 'username' in session:
            try:
                # Get user object
                user = User.get_by_username(username)
                if user:
                    # Analyze the fire image using AI vision
                    current_app.logger.info("Starting fire image analysis...")
                    vision_analysis = analyze_fire_image(clean_image_data, current_app.logger)

                    if vision_analysis and vision_analysis != "Unable to analyze the fire image at this time.":
                        # Create a flame reading entry
                        current_app.logger.info("Creating flame reading...")

                        # Create a history entry for the flame reading
                        flame_question = f"Sacred fire vision captured on {timestamp}"
                        history_entry = user.history.add_reading(
                            question=flame_question,
                            hexagram=f"flame_vision_{timestamp}",
                            reading="",  # Will be filled by AI
                            divination_type="flame_reading"
                        )

                        if history_entry:
                            # Generate the flame reading using AI
                            flame_reading = generate_flame_reading(
                                vision_analysis=vision_analysis,
                                user=user,
                                logger=current_app.logger,
                                reading_id=history_entry.reading_id
                            )

                            # Update the history entry with the actual reading
                            history_entry._reading_string = flame_reading
                            history_entry.save()

                            # Add reading info to response
                            response_data.update({
                                'flame_reading_created': True,
                                'reading_id': history_entry.reading_id,
                                'reading_path': history_entry.reading_path,
                                'vision_analysis': vision_analysis,
                                'flame_reading': flame_reading
                            })

                            current_app.logger.info(f"Flame reading created: {history_entry.reading_id}")
                        else:
                            current_app.logger.warning("Failed to create flame reading history entry")
                    else:
                        current_app.logger.warning("Vision analysis failed or returned error")
                        response_data['vision_analysis_error'] = "Unable to analyze fire image"
                else:
                    current_app.logger.warning(f"User not found: {username}")

            except Exception as e:
                current_app.logger.error(f"Error creating flame reading: {e}")
                response_data['flame_reading_error'] = str(e)

        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error(f"Error saving fire image: {e}")
        return jsonify({'error': 'Failed to save fire image'}), 500
