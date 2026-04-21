import os
import base64
import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for STM32/ESP-01S communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route for quick health check
@app.get("/")

async def root():
    return {"status": "success", "message": "Recycling AI Backend is Online"}

@app.post("/api/predict")
async def debug_endpoint(payload: dict):
    print(f"Received data from STM32: {payload}") # This shows up in Vercel Logs
    return {"status": "received", "data": payload}
async def classify_waste(file: UploadFile = File(...)):
    try:
        # Check for API Key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return {"status": "error", "message": "API Key missing in Vercel settings"}

        # Read and encode audio
        audio_bytes = await file.read()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://vercel.com",
            "X-Title": "Smart Recycling Station",
            "Content-Type": "application/json"
        }

        # Using a fast, free multimodal model
        payload = {
            "model": "google/gemma-3-4b-it:free", 
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Classify this audio into one word: PLASTIC, PAPER, METAL, or ORGANIC."},
                        {"type": "input_audio", "input_audio": {"data": audio_b64, "format": "wav"}}
                    ]
                }
            ]
        }

        # 8-second timeout to return a response before Vercel kills the process
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=8
        )
        
        if response.status_code != 200:
            return {"status": "error", "message": f"OpenRouter Error {response.status_code}"}

        data = response.json()
        category = data['choices'][0]['message']['content'].strip().upper()
        
        return {"status": "success", "category": category}

    except Exception as e:
        return {"status": "error", "message": str(e)}
