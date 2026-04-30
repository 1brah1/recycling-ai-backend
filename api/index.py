import os
import wave
import base64
import requests
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "success", "message": "Recycling AI Backend is Online"}

@app.post("/api/predict")
async def predict_endpoint(request: Request):
    try:
        # 1. Capture RAW BYTES from STM32 (Essential for audio)
        audio_bytes = await request.body()
        
        # 2. Log details for debugging
        byte_count = len(audio_bytes)
        print(f"!!! RECEIVED FROM STM32: {byte_count} bytes")

        if byte_count == 0:
            return {"status": "error", "message": "Empty body received"}

        # 3. Optional: Save as a .wav file to check quality
        # 16000Hz, 8-bit Mono (Matches STM32 settings)
        with wave.open("latest_record.wav", "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(1) # 1 byte for 8-bit
            wav_file.setframerate(16000)
            wav_file.writeframes(audio_bytes)

        # 4. Return success to STM32
        return {
            "status": "success",
            "message": f"Received {byte_count} bytes",
            "filename": "latest_record.wav"
        }
        
    except Exception as e:
        print(f"Crash error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/api/classify")
async def classify_waste(file: UploadFile = File(...)):
    """
    This route remains for manual uploads via Postman or Web Frontend
    """
    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return {"status": "error", "message": "API Key missing"}

        audio_bytes = await file.read()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

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

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        data = response.json()
        category = data['choices'][0]['message']['content'].strip().upper()
        
        return {"status": "success", "category": category}

    except Exception as e:
        return {"status": "error", "message": str(e)}
