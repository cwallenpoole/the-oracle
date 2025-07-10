#!/usr/bin/env python3
"""
Test script to verify Ollama integration with The Oracle.
"""

import os
import sys
from dotenv import load_dotenv

# Set up environment for testing
os.environ['USE_OLLAMA_FOR_TEXT'] = 'true'
os.environ['OLLAMA_MODEL'] = 'openchat:7b'  # Use available model
os.environ['OLLAMA_HOST'] = 'http://localhost:11434'

# Load environment
load_dotenv()

# Import after setting environment variables
from logic.ai_readers import generate_text_with_llm, USE_OLLAMA_FOR_TEXT

def test_ollama_connection():
    """Test if Ollama is running and accessible"""
    try:
        import ollama
        client = ollama.Client(host=os.environ.get('OLLAMA_HOST', 'http://localhost:11434'))

        # Test simple request
        response = client.chat(
            model=os.environ.get('OLLAMA_MODEL', 'llama3.2'),
            messages=[
                {"role": "user", "content": "Say hello in one word."}
            ]
        )

        print("✓ Ollama connection successful!")
        print(f"Response: {response['message']['content']}")
        return True

    except Exception as e:
        print(f"✗ Ollama connection failed: {e}")
        return False

def test_text_generation():
    """Test the integrated text generation function"""
    try:
        system_prompt = "You are a helpful assistant."
        user_prompt = "Say hello in exactly 3 words."

        response = generate_text_with_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=50
        )

        print("✓ Text generation successful!")
        print(f"Response: {response}")
        return True

    except Exception as e:
        print(f"✗ Text generation failed: {e}")
        return False

def main():
    print("Testing Ollama Integration with The Oracle")
    print("=" * 50)

    print("Configuration:")
    print(f"  USE_OLLAMA_FOR_TEXT: {USE_OLLAMA_FOR_TEXT}")
    print(f"  OLLAMA_MODEL: {os.environ.get('OLLAMA_MODEL', 'Not set')}")
    print(f"  OLLAMA_HOST: {os.environ.get('OLLAMA_HOST', 'Not set')}")
    print()

    # Test Ollama connection
    print("1. Testing Ollama connection...")
    ollama_works = test_ollama_connection()
    print()

    # Test text generation
    print("2. Testing integrated text generation...")
    generation_works = test_text_generation()
    print()

    print("=" * 50)
    if ollama_works and generation_works:
        print("✓ All tests passed! Ollama integration is working correctly.")
        print("\nTo use Ollama for text generation, set these environment variables:")
        print("  export USE_OLLAMA_FOR_TEXT=true")
        print("  export OLLAMA_MODEL=llama3.2")
        print("  export OLLAMA_HOST=http://localhost:11434")
    else:
        print("✗ Some tests failed. Please check your Ollama installation.")
        print("\nMake sure:")
        print("  - Ollama is installed and running")
        print("  - The specified model is available")
        print("  - Ollama is accessible at the specified host")

if __name__ == "__main__":
    main()
