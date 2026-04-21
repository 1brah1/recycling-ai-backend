import os
import base64
import requests
from fastapi import FastAPI, UploadFile, File

app = FastAPI()

# Your OpenRouter API Key (Set this in Vercel Dashboard)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.post("/api/classify")
async def classify_waste(file: UploadFile = File(...)):
    try:
        # 1. Read the audio file sent from STM32
        audio_bytes = await file.read()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        # 2. Call OpenRouter
        # Using Gemma 3 12B as it's a multimodal free model
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = (
            "You are a recycling assistant. Listen to this audio recording of a user describing an item. "
            "Classify it into exactly one of these categories: PLASTIC, PAPER, METAL, or ORGANIC. "
            "Return ONLY the category name in all caps."
        )

        payload = {
            "model": "google/gemma-3-12b-it:free", 
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "input_audio",
                            "input_audio": {"data": audio_b64, "format": "wav"}
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        data = response.json()
        category = data['choices'][0]['message']['content'].strip()

        return {"status": "success", "category": category}

    except Exception as e:
        return {"status": "error", "message": str(e)}