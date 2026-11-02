import asyncio
import base64
from backend.app.vision import extract_harvest_data

async def test_extraction():
    image_path = "samples/sample_harvest.jpg"
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    print(f"Sending image from {image_path} to Ollama...")
    try:
        result = await extract_harvest_data(image_bytes)
        print("Extraction Result:")
        print(result)
        
        fur_type = result.get("fur_type")
        print(f"\n--- Test Result ---")
        print(f"Extracted Fur Type: {fur_type}")
    except Exception as e:
        print(f"Error during extraction: {e}")

if __name__ == "__main__":
    asyncio.run(test_extraction())
