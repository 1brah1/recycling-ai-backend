import os
import base64
import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.post("/api/classify")
async def classify_waste(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        # Use a very specific, fast free model
        # Gemma 3 4B is much faster than 27B and stays under the 10s limit
        model_choice = "google/gemma-3-4b-it:free" 

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://vercel.com", # Required by some OpenRouter models
            "Content-Type": "application/json"
        }

        prompt = "Classify this audio into: PLASTIC, PAPER, METAL, or ORGANIC. Return one word."

        payload = {
            "model": model_choice,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "input_audio", "input_audio": {"data": audio_b64, "format": "wav"}}
                    ]
                }
            ],
            "timeout": 8 # Tell OpenRouter to hurry up
        }

        # Use a 9-second timeout so Vercel doesn't kill us first
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions", 
            headers=headers, 
            json=payload,
            timeout=9 
        )
        
        if response.status_code != 200:
            return {"status": "error", "message": f"OpenRouter Error: {response.text}"}

        data = response.json()
        ai_answer = data['choices'][0]['message']['content'].strip().upper()

        return {"status": "success", "category": ai_answer}

    except requests.exceptions.Timeout:
        return {"status": "error", "message": "AI took too long. Try a shorter recording."}
    except Exception as e:
        return {"status": "error", "message": str(e)}