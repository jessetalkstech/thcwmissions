import httpx
import json
import base64
from app.config import settings
from fastapi import HTTPException

async def extract_harvest_data(image_bytes: bytes) -> dict:
    model_name = settings.OLLAMA_MODEL_NAME
    
    # Encode image to base64
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    payload = {
        "model": model_name,
        "prompt": "Identify the following details from the harvest screenshot. Note that if an animal was shot multiple times, there will be multiple 'orange bar' sections. Each section has a player name above it, a list of organs and damage % inside it, and fields for weapon, ammo, distance, and weapon score underneath it. If multiple hit sections exist, aggregate the organs into the 'trophy_organs' and 'organs_high' lists. For 'weapon', 'ammo', 'distance', and 'weapon_score', use the values from the final hit section. Return the result strictly as a JSON object with the following keys: 'species' (string), 'location' (string), 'class' (string), 'gender' (string), 'weight' (float), 'fur_type' (string), 'tracking_distance' (float), 'difficulty' (string), 'trophy_type' (string), 'trophy_organs' (list), 'trophy_tier' (string), 'trophy_rating' (string), 'harvest_checks' (list of 4 booleans where True=green/passed, False=red/failed), 'xp' (int), 'cash' (int), 'session_score' (int), 'organs_high' (list), 'weapon' (string), 'ammo' (string), 'distance' (float), 'weapon_score' (int).",
        "stream": False,
        "format": "json",
        "images": [image_base64]
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                settings.OLLAMA_API_BASE,
                json=payload
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Ollama error: {response.text}")
            
            result = response.json()
            content = result.get("response", "{}")
            return json.loads(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to extract data: {str(e)}")
