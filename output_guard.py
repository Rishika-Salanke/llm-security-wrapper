import re
import difflib

class OutputGuard:
    """
    Layer 4: Output Guard (Semantic Check + DLP)
    Responsibility: Prevent system rule leaks and redact sensitive PII.
    """
    def __init__(self, system_prompt: str):
        # Layer 4.1: Secret Baseline
        self.secret_anchor = system_prompt.strip().lower()
        self.threshold = 0.7 
        
        # Layer 4.2: High-Impact DLP Patterns
        self.dlp_patterns = {
            "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
            "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "API_KEY": r"sk-[a-zA-Z0-9]{32,}",
        }

    def scan_semantic_leak(self, llm_output: str) -> dict:
        """
        Calculates mathematical similarity to detect rule leakage.
        """
        clean_output = llm_output.strip().lower()
        matcher = difflib.SequenceMatcher(None, self.secret_anchor, clean_output)
        similarity_score = matcher.ratio()
        
        print(f"[🔍 LAYER 4.1 LOG] Similarity Score: {similarity_score:.4f}")

        if similarity_score > self.threshold:
            return {
                "safe": False,
                "reason": f"Semantic Leak Detected (Similarity: {similarity_score:.2%})"
            }
        return {"safe": True}

    def redact_sensitive_data(self, text: str) -> str:
        """
        Scans and blackouts high-impact data like credit cards and emails.
        """
        redacted_text = text
        found_data = False
        
        for label, pattern in self.dlp_patterns.items():
            if re.search(pattern, redacted_text):
                redacted_text = re.sub(pattern, f"[REDACTED_{label}]", redacted_text)
                found_data = True
        
        if found_data:
            print(f"[🔍 LAYER 4.2 LOG] Sensitive data redacted.")
        
        return redacted_text