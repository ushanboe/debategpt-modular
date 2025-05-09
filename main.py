from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import time

app = FastAPI()

# CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://localhost:11434"

@app.get("/models")
def list_models():
    try:
        res = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        res.raise_for_status()
        models = sorted([m["name"] for m in res.json().get("models", [])])
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/{model_name}")
def check_model(model_name: str):
    try:
        res = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        res.raise_for_status()
        models = [m["name"] for m in res.json().get("models", [])]
        return {"exists": model_name in models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/{model_name}/pull")
def pull_model(model_name: str):
    try:
        with requests.post(f"{OLLAMA_URL}/api/pull", json={"name": model_name}, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    pass  # Could log pull progress
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat(payload: dict):
    try:
        res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
