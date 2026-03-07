import os
import httpx
import logging
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from logging.handlers import RotatingFileHandler

# 1. LOAD CONFIGURATION
load_dotenv()
LLM_API_URL = os.getenv("BASE_LLM_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
SEMANTIC_THRESHOLD = float(os.getenv("SEMANTIC_THRESHOLD", 0.7))
API_KEY = os.getenv("GROQ_API_KEY")
ENABLE_LOGS = os.getenv("ENABLE_FILE_LOGGING", "True").lower() == "true"

# 2. INITIALIZE LOGGING (OPTIONAL FILE WRITING)
handlers = [logging.StreamHandler()] # Always show in terminal

if ENABLE_LOGS:
    if not os.path.exists('logs'):
        os.makedirs('logs')
    # Add the file handler only if enabled
    handlers.append(RotatingFileHandler("logs/security_audit.log", maxBytes=1000000, backupCount=5))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] ShieldProxy: %(message)s',
    handlers=handlers
)
logger = logging.getLogger("ShieldProxy")

# 3. IMPORT & INITIALIZE DEFENSE LAYERS
from layers.sanitizer import InputSanitizer
from layers.context_manager import ContextManager
from layers.policy_engine import PolicyEngine 
from layers.output_guard import OutputGuard  

app = FastAPI(title="ShieldProxy Middleware", version="1.0")

sanitizer = InputSanitizer()
policy_engine = PolicyEngine("ruleFile.yaml") 
context_engine = ContextManager()
output_guard = OutputGuard(context_engine.system_anchor)

# 4. PROXY MODELS
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]

# 5. CORE LLM FORWARDER
async def call_llm(messages: list):
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        logger.info(f"🚀 Forwarding request to: {LLM_API_URL}")
        response = await client.post(
            LLM_API_URL,
            headers=headers,
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False 
            },
            timeout=60.0
        )
        return response.json()

# 6. EXCEPTION HANDLER
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("🚨 Blocked: Malicious Syntax detected.")
    return JSONResponse(
        status_code=400,
        content={"choices": [{"message": {"role": "assistant", "content": "🛡️ BLOCK: Malicious syntax detected."}}]}
    )

# 7. THE PROXY ENDPOINT
@app.post("/v1/chat/completions")
async def chat_proxy(request: ChatRequest):
    raw_prompt = request.messages[-1].content
    
    # --- LAYER 1: SANITIZATION ---
    clean_prompt = sanitizer.sanitize(raw_prompt)
    logger.info("✅ Layer 1: Sanitized.")

    # --- LAYER 2: AI POLICY SCAN ---
    policy_decision = policy_engine.evaluate(clean_prompt)
    if policy_decision.ai_scan:
        scan = policy_decision.ai_scan
        logger.info(f"🧠 Layer 2 AI Scan: Label={scan['label']}, Score={scan['score']:.4f}")

    if not policy_decision.allowed:
        logger.warning(f"❌ BLOCKED: {policy_decision.reason}")
        return {"choices": [{"message": {"role": "assistant", "content": policy_decision.reason}}]}
    
    # --- LAYER 3: CONTEXT ANCHORING ---
    reinforced_prompt = context_engine.reinforce(clean_prompt)

    # --- LLM EXECUTION ---
    request.messages[-1].content = reinforced_prompt
    llm_response = await call_llm(request.dict()["messages"])
    
    # --- OUTPUT EXTRACTION ---
    try:
        raw_output_text = llm_response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        logger.error("⚠️ LLM Parse Error.")
        return llm_response

    # --- LAYER 4.1: SEMANTIC LEAK GUARD ---
    exit_check = output_guard.scan_semantic_leak(raw_output_text)
    if not exit_check["safe"]:
        logger.warning(f"🚨 LAYER 4.1 BLOCK: {exit_check['reason']}")
        return {"choices": [{"message": {"role": "assistant", "content": "🛡️ SECURITY BLOCK: Internal info leak detected."}}]}

    # --- LAYER 4.2: DLP REDACTION ---
    final_clean_text = output_guard.redact_sensitive_data(raw_output_text)
    llm_response["choices"][0]["message"]["content"] = final_clean_text
    
    if final_clean_text != raw_output_text:
        logger.info("📝 Layer 4.2: Data Redacted.")

    logger.info("🟢 Final Response Delivered.")
    return llm_response