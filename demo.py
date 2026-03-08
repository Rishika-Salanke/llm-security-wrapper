import streamlit as st
import requests
import os
import time
from dotenv import load_dotenv

# Load your default Groq key from the .env file as a backup
load_dotenv()
DEFAULT_API_KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="ShieldProxy Demo", page_icon="🛡️", layout="wide")

# --- SIDEBAR: ONLY BYOK CONFIGURATION NOW ---
with st.sidebar:
    st.header("⚙️ Configuration (BYOK)")
    st.markdown("Use your own API and Model:")
    
    # User Inputs for their own model and key
    custom_url = st.text_input("Base API URL", value="https://api.groq.com/openai/v1/chat/completions")
    custom_model = st.text_input("Model Name", value="llama-3.1-8b-instant")
    custom_key = st.text_input("API Key", type="password", help="Leave blank to use default server key")

st.title("🛡️ ShieldProxy Demo")
st.markdown("Compare an unprotected LLM against our 4-Layer Security Middleware.")

# The Magic Switch for the Before/After Demo
mode = st.radio(
    "Select Connection Mode:", 
    ["🔴 Direct to LLM (Unprotected)", "🟢 Through ShieldProxy (Protected)"]
)

# Chat history memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Input box for the user (Back to manual typing only!)
if prompt := st.chat_input("Type your prompt here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Figure out which API key to use (User's or Default)
    active_key = custom_key if custom_key else DEFAULT_API_KEY

    # Route the request based on the switch
    if "Protected" in mode:
        url = "http://localhost:8000/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "X-Target-Url": custom_url,
            "X-Target-Model": custom_model,
            "X-Target-Key": active_key
        }
        payload = {"model": custom_model, "messages": st.session_state.messages}
    else:
        url = custom_url
        headers = {
            "Authorization": f"Bearer {active_key}", 
            "Content-Type": "application/json"
        }
        payload = {"model": custom_model, "messages": st.session_state.messages}

    # Fetch the response
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=payload).json()
        latency = time.time() - start_time
        
        if "error" in response:
            reply = f"🚨 **BLOCKED BY SHIELDPROXY:** {response['error']}"
        elif "choices" in response:
            reply = response["choices"][0]["message"]["content"]
        else:
            reply = f"⚠️ Unexpected response: {response}"
            
    except Exception as e:
        reply = f"⚠️ Connection Error: Is your ShieldProxy server running? ({e})"
        latency = 0.0

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").write(reply)
    
    if latency > 0:
        st.caption(f"⏱️ **Response Time:** {latency:.2f} seconds")

# Add a clear button to reset the demo
if st.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()