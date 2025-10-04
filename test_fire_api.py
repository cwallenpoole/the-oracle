#!/usr/bin/env python3
"""
Simple test script for the fire image saving API
"""
import requests
import base64
import json
import os
from PIL import Image, ImageDraw

def create_test_image():
    """Create a simple test image"""
    # Create a 400x300 image with a fire-like pattern
    img = Image.new('RGB', (400, 300), color='black')
    draw = ImageDraw.Draw(img)

    # Draw some simple shapes to simulate fire
    draw.rectangle([150, 250, 250, 280], fill='red')
    draw.ellipse([140, 200, 260, 270], fill='orange')
    draw.ellipse([160, 180, 240, 240], fill='yellow')

    # Save as temporary file
    temp_path = 'test_fire.png'
    img.save(temp_path)

    # Convert to base64
    with open(temp_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    # Clean up
    os.remove(temp_path)

    return f"data:image/png;base64,{image_data}"

def test_fire_api():
    """Test the fire image saving API"""
    # Create test image
    test_image = create_test_image()

    # Prepare test data
    test_data = {
        'image': test_image,
        'metadata': {
            'timestamp': '2025-01-23T12:00:00.000Z',
            'width': 400,
            'height': 300,
            'type': 'test_fire_image'
        }
    }

    # Test the API endpoint
    try:
        response = requests.post(
            'http://localhost:5000/api/save-fire-image',
            headers={'Content-Type': 'application/json'},
            json=test_data
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ API Test Successful!")
            print(f"Response: {json.dumps(result, indent=2)}")

            # Check if image URL is provided
            if 'image_url' in result:
                print(f"🔥 Image URL: {result['image_url']}")
                print(f"📁 Filename: {result['filename']}")
            else:
                print("⚠️  Warning: No image_url in response")

        else:
            print(f"❌ API Test Failed: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the Flask app is running on localhost:5000")
    except Exception as e:
        print(f"❌ Test Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Fire Image API...")
    test_fire_api()
