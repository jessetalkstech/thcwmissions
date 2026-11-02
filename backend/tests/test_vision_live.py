import asyncio
import httpx
import json
import os
from app.config import settings
from app.vision import extract_harvest_data

async def test_vision_live():
    # Create a dummy image file for testing
    test_img = "test_harvest.png"
    with open(test_img, "wb") as f:
        f.write(b"dummy image content that might not be valid but enough to test the connection")

    print(f"Testing connection to Ollama at {settings.OLLAMA_API_BASE} using {settings.OLLAMA_MODEL_NAME}...")
    
    try:
        with open(test_img, "rb") as f:
            data = f.read()
            result = await extract_harvest_data(data)
            print(f"Successfully received response: {result}")
            print("Test Passed!")
    except Exception as e:
        print(f"Test Failed: {e}")
        print("Ensure your Ollama instance is running and the IP/Port in .env.example is correct.")
    finally:
        if os.path.exists(test_img):
            os.remove(test_img)

if __name__ == "__main__":
    asyncio.run(test_vision_live())
