from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import List

# 1. IMPORT BOTH LAYERS
from layers.sanitizer import InputSanitizer
from layers.security_model import InjectionClassifier # Updated import

# 2. Initialize the App and BOTH Defense Layers
app = FastAPI(title="LLM Security Wrapper", version="1.0")
sanitizer = InputSanitizer()
guard = InjectionClassifier() # Layer 2 initialized here!

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"choices": [{"message": {"role": "assistant", "content": "🛡️ BLOCK: Malicious syntax detected."}}]}
    )

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]

# 4. The Proxy Endpoint
@app.post("/v1/chat/completions")
async def chat_proxy(request: ChatRequest):
    raw_prompt = request.messages[-1].content
    
    # --- STEP 1: APPLY LAYER 1 (The Janitor) ---
    clean_prompt = sanitizer.sanitize(raw_prompt)
    
    print(f"\n[🛡️ LAYER 1 LOG] Cleaned: {clean_prompt}")

    # --- STEP 2: APPLY LAYER 2 (The AI Guard) ---
    # We pass the CLEANED prompt to the AI to check for intent
    security_check = guard.is_safe(clean_prompt)
    
    print(f"[🧠 LAYER 2 LOG] Label: {security_check['label']} | Score: {security_check['score']:.4f}")

    # --- STEP 3: SECURITY DECISION ---
    if not security_check["safe"]:
        return {
            "choices": [{
                "message": {
                    "role": "assistant", 
                    "content": f"🛡️ SECURITY BLOCK: Semantic attack detected (AI Confidence: {security_check['score']:.2f})."
                }
            }]
        }

    # Mock Response (If both layers pass)
    return {
        "choices": [{"message": {"role": "assistant", "content": f"Secure Proxy processed: '{clean_prompt}'"}}]
    }