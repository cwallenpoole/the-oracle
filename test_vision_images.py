#!/usr/bin/env python3
"""
Test script for vision image generation system
"""
import json
import requests
import time
from datetime import datetime

def test_vision_generation():
    """Test the vision image generation API"""

    # Sample test data
    test_data = {
        'reading_id': 'test_reading_123',
        'fire_image_filename': 'test_fire.png',
        'visions': [
            'Luminous Butterfly',
            'Whispering Leaf',
            'Twisting Serpent',
            'Shimmering Chalice',
            'Eclipsing Shadow'
        ]
    }

    base_url = 'http://localhost:5000'

    print("🧪 Testing Vision Image Generation API...")
    print(f"Test data: {json.dumps(test_data, indent=2)}")

    try:
        # Step 1: Start vision generation
        print("\n1️⃣ Starting vision generation...")
        response = requests.post(
            f'{base_url}/api/generate-vision-images',
            headers={'Content-Type': 'application/json'},
            json=test_data
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                generation_id = result['generation_id']
                expected_images = result['expected_images']
                print(f"✅ Generation started successfully!")
                print(f"📍 Generation ID: {generation_id}")
                print(f"🎨 Expected images: {expected_images}")

                # Step 2: Check generation status
                print(f"\n2️⃣ Checking generation status...")
                max_checks = 30  # Wait up to 5 minutes (30 * 10 seconds)
                check_count = 0

                while check_count < max_checks:
                    time.sleep(10)  # Wait 10 seconds between checks
                    check_count += 1

                    status_response = requests.get(
                        f'{base_url}/api/vision-images-status/{generation_id}'
                    )

                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        completed_images = status_data.get('completed_images', [])

                        print(f"⏳ Check {check_count}/{max_checks}: {len(completed_images)}/{expected_images} images completed")

                        if len(completed_images) >= expected_images:
                            print(f"🎉 All images generated successfully!")
                            print("Generated images:")
                            for img in completed_images:
                                print(f"  🖼️  {img['vision']}: {img['url']}")
                            break
                        elif len(completed_images) > 0:
                            print(f"📈 Progress: {completed_images[-1]['vision']} completed")
                    else:
                        print(f"⚠️  Status check failed: {status_response.status_code}")

                if check_count >= max_checks:
                    print("⏰ Timeout: Generation taking longer than expected")

            else:
                print(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the Flask app is running on localhost:5000")
        print("💡 You also need to be logged in to test this API")
    except Exception as e:
        print(f"❌ Test Error: {e}")

def test_vision_extraction():
    """Test vision extraction from sample reading text"""
    sample_reading = """
    The flames dance with ancient wisdom, revealing visions that speak to your deepest questions.

    In the dancing fire, I saw a Luminous Butterfly emerging from the depths, its wings shimmering
    with ethereal light. The vision of a Whispering Leaf appeared next, its surface inscribed with
    sacred symbols that seem to shift and change.

    As the flames grew higher, a Twisting Serpent manifested, coiling around an invisible staff.
    The Shimmering Chalice appeared in the center, overflowing with liquid starlight. Finally,
    the Eclipsing Shadow revealed itself, showing the balance between light and darkness.
    """

    print("🔍 Testing Vision Extraction...")
    print("Sample reading text:")
    print(sample_reading)

    # Import the extraction function
    import sys
    sys.path.append('/Users/christopher.poole/the-oracle')

    try:
        from routes.api import _extract_visions_from_text

        visions = _extract_visions_from_text(sample_reading)
        print(f"\n✅ Extracted {len(visions)} visions:")
        for i, vision in enumerate(visions, 1):
            print(f"  {i}. {vision}")

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Extraction error: {e}")

if __name__ == "__main__":
    print("🎨 Vision Image Generation Test Suite")
    print("=" * 50)

    # Test vision extraction (doesn't require server)
    test_vision_extraction()

    print("\n" + "=" * 50)

    # Test full API (requires running server and authentication)
    print("\n⚠️  Note: The API test requires:")
    print("1. Flask app running on localhost:5000")
    print("2. User to be logged in")
    print("3. OpenAI API key configured")
    print("4. Sufficient OpenAI credits")

    user_input = input("\nProceed with API test? (y/n): ")
    if user_input.lower() == 'y':
        test_vision_generation()
    else:
        print("👋 API test skipped")
