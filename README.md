# 🛡️ ShieldProxy — LLM Security Middleware

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

Enterprise-grade, 4-layer asynchronous security middleware for Large Language Models.

ShieldProxy acts as a transparent, drop-in proxy between client applications and LLM providers (Groq, OpenAI, Anthropic, Ollama). It intercepts traffic at the network layer, sanitizes inputs, evaluates prompts for malicious intent, enforces system-level constraints, and prevents data exfiltration — all in real-time.

---

## 📊 Performance Metrics

| Metric | Result |
|--------|--------|
| Attack Block Rate | 95.2% |
| False Positive Rate | 0% |
| API Latency Reduction | 445ms per attack via Fail-Fast routing |
| Test Dataset | 50 adversarial prompts |

---

## 🏗️ Architecture Overview

ShieldProxy uses a **Bring Your Own Key (BYOK)** architecture. It mimics the standard OpenAI `/v1/chat/completions` endpoint, allowing existing applications to route traffic through the proxy without changing their underlying code.

Routing and provider selection are handled dynamically per request via custom HTTP headers, making the proxy completely **provider-agnostic**.

---

## 🔐 The 4-Layer Defense Engine

Every request and response passes through a sequential, fail-fast security pipeline:

### Layer 1 — Input Sanitization
- Normalizes character encodings
- Strips invisible control characters, zero-width spaces, and bypass artifacts
- Mitigates token-smuggling attacks

### Layer 2 — AI Policy Scanner (Prompt Injection Defense)
- Semantically analyzes incoming prompts using a localized AI evaluator
- Detects role-play jailbreaks, system prompt overrides, and complex injection payloads
- Rejects requests exceeding the configured risk threshold

### Layer 3 — Context Anchoring
- Enforces strict boundaries on the LLM's operational scope
- Injects immutable system constraints into the prompt payload before it reaches the external provider
- Prevents context drift and hallucination vectors

### Layer 4 — Data Loss Prevention (DLP)
- Intercepts the LLM response before it reaches the client
- Scans for sensitive data — PII, API keys, internal network topologies
- Redacts or blocks the response entirely if data exfiltration is detected

---

## 📂 Project Structure

```
llm-security-wrapper/
├── layers/
│   ├── sanitizer.py          # Layer 1: Input normalization
│   ├── policy_engine.py      # Layer 2: Prompt injection detection
│   ├── context_manager.py    # Layer 3: Boundary enforcement
│   └── output_guard.py       # Layer 4: DLP & PII scanning
├── logs/
│   └── security_audit.log    # Audit trail
├── demo.py                   # Streamlit frontend — BYOK UI
├── server.py                 # FastAPI asynchronous gateway
├── ruleFile.yaml             # Configurable security thresholds
├── requirements.txt          # Dependencies
└── .env.example              # Environment template
```

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- pip package manager

### Steps

**1. Clone the repository:**
```bash
git clone https://github.com/Rishika-Salanke/llm-security-wrapper.git
cd llm-security-wrapper
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Configure environment:**
```bash
cp .env.example .env
```

Edit `.env` with your values:
```env
BASE_LLM_URL="http://localhost:11434/v1/chat/completions"
MODEL_NAME="dolphin3:8b"
SYSTEM_PROMPT="You are a helpful, professional, and harmless AI assistant."
SEMANTIC_THRESHOLD=0.5
LOG_FILE_PATH="logs/security_audit.log"
ENABLE_FILE_LOGGING=True
```

**4. Start the gateway:**
```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

**5. (Optional) Launch the Streamlit UI:**
```bash
streamlit run demo.py
```

---

## 💻 API Reference

ShieldProxy exposes a single unified endpoint:

```
POST /v1/chat/completions
```

### Dynamic Routing — BYOK Headers

| Header | Description | Example |
|--------|-------------|---------|
| `X-Target-Url` | LLM provider base URL | `https://api.groq.com/openai/v1/chat/completions` |
| `X-Target-Model` | Model ID to invoke | `llama-3.1-8b-instant` |
| `X-Target-Key` | Provider API key | `gsk_...` |

If headers are omitted, the server defaults to values in your `.env` file.

### Example cURL Request

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-Target-Url: https://api.groq.com/openai/v1/chat/completions" \
  -H "X-Target-Model: llama-3.1-8b-instant" \
  -H "X-Target-Key: YOUR_API_KEY" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### Security Response

If a request fails any layer, ShieldProxy terminates the connection instantly and returns:

```json
{
  "error": "AI Guard blocked: INJECTION (confidence: 99.35%)"
}
```

---

## ⚙️ Configuration

Security thresholds are configurable via `ruleFile.yaml`:

```yaml
semantic_threshold: 0.5   # 0 = permissive, 1 = most strict
```

Adjust based on your use case and acceptable false positive tolerance.

---

## 🖥️ Frontend UI

A Streamlit-based BYOK frontend is included in `demo.py`.

It allows real-time A/B testing — send the same prompt directly to an LLM and through ShieldProxy to compare responses and see blocks in action.

```bash
streamlit run demo.py
```

---

## 📋 Supported LLM Providers

ShieldProxy is provider-agnostic. Tested with:
- Groq
- OpenAI
- Ollama (local)
- Anthropic

Any provider following the OpenAI `/v1/chat/completions` schema works out of the box.

---

## 👩‍💻 Author

**Rishika Salanke K S**
- LinkedIn: [linkedin.com/in/rishikasalanke](https://linkedin.com/in/rishikasalanke)
- GitHub: [github.com/Rishika-Salanke](https://github.com/Rishika-Salanke)

**Saadhana M**
- LinkedIn: [linkedin.com/in/saadhana](https://www.linkedin.com/in/saadhana-m-b70867280/)
- GitHub: [github.com/Saadhana](https://github.com/Saadhana2342)