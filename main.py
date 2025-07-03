from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
print("✅ Loaded OPENROUTER_API_KEY:", OPENROUTER_API_KEY)

# Setup logging
logging.basicConfig(level=logging.INFO)

# In-memory database
class InMemoryDB:
    def __init__(self):
        self.data = {"health": [], "medications": [], "nutrition": []}
        self.counter = 1

    def insert(self, category, item):
        item["_id"] = str(self.counter)
        self.counter += 1
        self.data[category].append(item)
        return item["_id"]

    def get_all(self, category):
        return sorted(self.data[category], key=lambda x: x.get("date", ""), reverse=True)

db = InMemoryDB()

# Create FastAPI app
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Request models
class HealthMetric(BaseModel):
    date: str
    weight: Optional[float]
    blood_pressure: Optional[str]
    glucose_level: Optional[float]
    heart_rate: Optional[int]

class Medication(BaseModel):
    name: str
    dosage: str
    frequency: str
    start_date: str
    end_date: Optional[str]

class Nutrition(BaseModel):
    date: str
    calories: float
    protein: float
    carbs: float
    fat: float

class ChatInput(BaseModel):
    message: str

# Routes
@app.get("/")
async def serve_index():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except:
        raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/health")
async def get_health():
    return db.get_all("health")

@app.post("/health")
async def add_health(data: HealthMetric):
    try:
        item = {k: v for k, v in data.dict().items() if v is not None}
        _id = db.insert("health", item)
        return {"success": True, "id": _id}
    except:
        raise HTTPException(status_code=500, detail="Failed to add health metric")

@app.get("/medications")
async def get_meds():
    return db.get_all("medications")

@app.post("/medications")
async def add_med(data: Medication):
    try:
        _id = db.insert("medications", data.dict())
        return {"success": True, "id": _id}
    except:
        raise HTTPException(status_code=500, detail="Failed to add medication")

@app.get("/nutrition")
async def get_nutrition():
    return db.get_all("nutrition")

@app.post("/nutrition")
async def add_nutrition(data: Nutrition):
    try:
        _id = db.insert("nutrition", data.dict())
        return {"success": True, "id": _id}
    except:
        raise HTTPException(status_code=500, detail="Failed to add nutrition")

@app.post("/chatbot")
async def chatbot(input: ChatInput):
    if not OPENROUTER_API_KEY:
        return {"response": "❌ API key is missing. Please add it to your .env file."}

    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek/deepseek-chat-v3-0324",
            "messages": [
                {"role": "system", "content": "You are a helpful AI health assistant."},
                {"role": "user", "content": input.message}
            ],
            "max_tokens": 512
        }

        print("📨 Sending request to OpenRouter...")
        print(payload)

        async with httpx.AsyncClient() as client:
            res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            print("✅ Response from OpenRouter:", data)
            return {"response": data["choices"][0]["message"]["content"]}

    except httpx.HTTPStatusError as http_err:
        print(f"❌ HTTP error: {http_err.response.status_code}")
        print(http_err.response.text)
        return {"response": f"OpenRouter returned an error: {http_err.response.status_code}"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"response": "❌ Unexpected error occurred while contacting OpenRouter."}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

