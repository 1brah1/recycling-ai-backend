from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "success", "message": "The server is alive!"}

@app.get("/test-ai")
async def test():
    return {"message": "If you see this, the API is configured correctly."}
