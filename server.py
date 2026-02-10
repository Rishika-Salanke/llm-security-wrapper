from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


# IMPORT THE NEW MODULE
from layers.sanitizer import InputSanitizer

# 1. Initialize the App
app = FastAPI(title="LLM Security Wrapper", version="1.0")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # This catches the error that causes 'null'
    return JSONResponse(
        status_code=400,
        content={
            "choices": [{
                "message": {
                    "role": "assistant", 
                    "content": "🛡️ BLOCK: Malicious syntax or broken request detected."
                }
            }]
        }
    )

# 2. Initialize the Defense Layer
sanitizer = InputSanitizer()

# 3. Define Data Models
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
    
    # --- APPLY LAYER 1 ---
    clean_prompt = sanitizer.sanitize(raw_prompt)
    
    print(f"\n[🛡️ LAYER 1 LOG]")
    print(f"Original: {raw_prompt}")
    print(f"Cleaned : {clean_prompt}")

    # Mock Response (We will connect LLaMA later)
    return {
        "choices": [{"message": {"role": "assistant", "content": f"Secure Proxy processed: '{clean_prompt}'"}}]
    }