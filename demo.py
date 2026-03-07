import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load your Groq key from the .env file
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="ShieldProxy Demo", page_icon="🛡️")
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

# Input box for the user
if prompt := st.chat_input("Type your prompt here..."):
    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Route the request based on the switch
    if "Protected" in mode:
        # Goes to your local server (ShieldProxy)
        url = "http://localhost:8000/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
    else:
        # Goes straight to Groq (bypassing your security)
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}", 
            "Content-Type": "application/json"
        }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": st.session_state.messages
    }

    # Fetch the response
    try:
        response = requests.post(url, headers=headers, json=payload).json()
        
        # Check if the proxy blocked it and returned an error
        if "error" in response:
            reply = f"🚨 **BLOCKED BY SHIELDPROXY:** {response['error']}"
        elif "choices" in response:
            reply = response["choices"][0]["message"]["content"]
        else:
            reply = f"⚠️ Unexpected response: {response}"
            
    except Exception as e:
        reply = f"⚠️ Connection Error: Is your ShieldProxy server running? ({e})"

    # Save and show the AI's response
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").write(reply)

# Add a clear button to reset the demo
if st.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()