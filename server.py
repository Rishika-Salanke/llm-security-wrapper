from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import List
import httpx  # Ensure you ran: uv pip install httpx

# 1. IMPORT BOTH LAYERS
from layers.sanitizer import InputSanitizer
from layers.security_model import InjectionClassifier 
from layers.context_manager import ContextManager

# 2. Initialize the App and BOTH Defense Layers
app = FastAPI(title="LLM Security Wrapper", version="1.0")
sanitizer = InputSanitizer()
guard = InjectionClassifier() 
context_engine = ContextManager()

# 3. Ollama Configuration
# This is the local address where your "Sword" (the LLM) is listening
LLM_API_URL = "http://localhost:11434/v1/chat/completions"

async def call_llm(messages: list):
    """
    Sends the message history to Ollama and gets a real response.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            LLM_API_URL,
            json={
                "model": "gemma2:2b", # This must match the model you pulled
                "messages": messages,
                "stream": False 
            },
            timeout=60.0 # Give the LLM time to think
        )
        return response.json()

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
    
    # --- STEP 4: APPLY LAYER 3 (Context Reinforcement) ---
    # We wrap the clean prompt inside the permanent system rules
    reinforced_prompt = context_engine.reinforce(clean_prompt)
    
    # Update the request object so the LLM receives the anchored version
    request.messages[-1].content = reinforced_prompt

    # SUCCESS: CALL THE REAL LLM (Passing the anchored message)
    print(f"[🛡️ LAYER 3 LOG] Anchoring rules to user prompt...")


    # --- STEP 5: CALL THE REAL LLM ---
    # We replace the user's messy/dangerous prompt with our cleaned version
    request.messages[-1].content = reinforced_prompt
    
    print("[🚀] Security checks passed. Calling LLM...")
    llm_response = await call_llm(request.dict()["messages"])
    
    return llm_response