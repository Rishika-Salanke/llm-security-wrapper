from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import List
import httpx  # Ensure you ran: uv pip install httpx

# 1. IMPORT DEFENSE LAYERS
from layers.sanitizer import InputSanitizer
from layers.context_manager import ContextManager
# We only need PolicyEngine now, as it loads the AI Guard internally!
from policy_engine import PolicyEngine 
from output_guard import OutputGuard  


# 2. Initialize the App and Defense Layers
app = FastAPI(title="LLM Security Wrapper", version="1.0")
sanitizer = InputSanitizer()
policy_engine = PolicyEngine("ruleFile.yaml") # Using the correct YAML file
context_engine = ContextManager()
output_guard = OutputGuard(context_engine.system_anchor)


# 3. Ollama Configuration
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

    # --- STEP 2: APPLY MERGED LAYER 2 (AI Guard + Policy) ---
    # The Policy Engine automatically runs the AI Guard AND handles quarantine logging!
    policy_decision = policy_engine.evaluate(clean_prompt)
    
    # Print the AI score to your terminal if the AI scan ran
    if policy_decision.ai_scan:
        scan = policy_decision.ai_scan
        print(f"[🧠 LAYER 2 LOG] Label: {scan['label']} | Score: {scan['score']:.4f}")

    # --- STEP 3: SECURITY DECISION ---
    # We use dot notation (.allowed and .reason) because it returns a dataclass object
    if not policy_decision.allowed:
        return {
            "choices": [{
                "message": {
                    "role": "assistant", 
                    "content": policy_decision.reason  # Uses your teammate's custom messages!
                }
            }]
        }
    
    # --- STEP 4: APPLY LAYER 3 (Context Reinforcement) ---
    # We wrap the clean prompt inside the permanent system rules
    print(f"[🛡️ LAYER 3 LOG] Anchoring rules to user prompt...")
    reinforced_prompt = context_engine.reinforce(clean_prompt)

   # --- STEP 5: CALL THE REAL LLM ---
    # We replace the user's messy/dangerous prompt with our secured, anchored version
    request.messages[-1].content = reinforced_prompt
    
    print("[🚀] Security checks passed. Calling LLM...")
    llm_response = await call_llm(request.dict()["messages"])
    
    # --- EXTRACTION STEP  ---

    try:
        # We must extract the string content from the LLM JSON response
        raw_output_text = llm_response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        # If the LLM response is malformed, we return an error instead of crashing
        print("[⚠️] Error parsing LLM response.")
        return llm_response

    # --- STEP 6: APPLY LAYER 4.1 (The Semantic Guard) ---
    print(f"[🔍] Running Layer 4.1 Semantic Check on: {raw_output_text[:50]}...")
    exit_check = output_guard.scan_semantic_leak(raw_output_text)
    
    if not exit_check["safe"]:
        print(f"[🚨 LAYER 4.1 BLOCK] {exit_check['reason']}")
        return {
            "choices": [{
                "message": {
                    "role": "assistant", 
                    "content": "🛡️ SECURITY BLOCK: Response contains internal system information."
                }
            }]
        }

    # --- STEP 7: APPLY LAYER 4.2 (DLP Redaction) ---
    # We redact the text instead of blocking the whole response
    final_clean_text = output_guard.redact_sensitive_data(raw_output_text)
    
    # Update the final response object with the safe text
    llm_response["choices"][0]["message"]["content"] = final_clean_text
    
    # SUCCESS: Return the clean response
    print("[✅] Response is safe. Delivering to user.")
    return llm_response