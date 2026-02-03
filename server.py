from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

# 1. Initialize the Server
app = FastAPI(title="LLM Security Wrapper", version="1.0")

# 2. Define the Data Structure (Matches OpenAI's format) [cite: 460]
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]

# 3. The "Reverse Proxy" Endpoint
@app.post("/v1/chat/completions")
async def chat_proxy(request: ChatRequest):
    # This is where your 5 Defense Layers will sit
    user_prompt = request.messages[-1].content
    
    print(f"\n[🔁 RECEIVED] Request for model: {request.model}")
    print(f"[📨 INPUT] User says: {user_prompt}")

    # --- PLACEHOLDER FOR DEFENSE LAYERS ---
    # clean_prompt = input_sanitization(user_prompt)
    # if detect_injection(clean_prompt): return "Blocked"
    # ...
    # --------------------------------------

    # 4. Mock Response (Simulating the LLM for now)
    return {
        "id": "gen-123",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": f"Secure Proxy received: '{user_prompt}'"
            }
        }]
    }