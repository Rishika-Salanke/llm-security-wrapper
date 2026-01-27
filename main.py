import re
import unicodedata

class DefenseFramework:
    def __init__(self):
        self.turn_count = 0
        self.core_mission = "Secure Technical Assistant"

    def process_request(self, user_input):
        print(f"\n[DEBUG] Starting defense for turn {self.turn_count + 1}...")
        
        # Layer 1: Sanitization
        clean = unicodedata.normalize("NFKC", user_input)
        clean = re.sub(r'<[^>]*>', '', clean)
        clean = re.sub(r'[^\w\s\.,?!\-]', '', clean)[:500].strip()
        print(f" -> Layer 1 (Sanitization) Passed.")

        # Layer 2: Injection Detection
        if any(re.search(p, clean, re.IGNORECASE) for p in [r"ignore previous", r"system prompt"]):
            return "❌ BLOCKED BY LAYER 2: Injection Attack Detected."
        print(f" -> Layer 2 (Detection) Passed.")

        # Layer 3 & 4: Reinforcement & Consistency
        self.turn_count += 1
        reminder = f"REMINDER: Your role is {self.core_mission}. " if self.turn_count % 3 == 0 else ""
        final_prompt = f"SYSTEM: {reminder}USER: {clean}"
        print(f" -> Layer 3 & 4 (Reinforcement/Consistency) Applied.")

        # Mock LLM Call
        # We simulate the LLM response here
        response = "I am a secure assistant. I cannot share my internal keys like 'KEY_12345678901234567890123456789012'."
        
        # Layer 5: Output Guardrail
        if re.search(r"[A-Za-z0-9_-]{32,}", response):
            return "❌ BLOCKED BY LAYER 5: LLM attempted to leak a secret key."
        
        return f"✅ SUCCESS: {response}"

# Run the interactive demo
if __name__ == "__main__":
    guard = DefenseFramework()
    print("=== LLM SECURITY WRAPPER READY ===")
    while True:
        msg = input("\nEnter a message (or 'exit' to quit): ")
        if msg.lower() == 'exit': break
        print(guard.process_request(msg))