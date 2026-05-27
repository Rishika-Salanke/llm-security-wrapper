import ftfy
import base64
import urllib.parse
import re
import html

class InputSanitizer:
    """
    Layer 1: Input Sanitization (Pre-LLM)
    Responsibility: Canonicalization and Structural Neutralization.
    """
    
    def sanitize(self, text: str) -> str:
        # 1. Canonicalization
        text = ftfy.fix_text(text)
        text = urllib.parse.unquote(text)
        text = html.unescape(text)
        
        # 2. Base64 Unmasking (Search and Replace)
        b64_pattern = r'[A-Za-z0-9+/]{12,}={0,2}'
        matches = re.findall(b64_pattern, text)
        for match in matches:
            try:
                decoded = base64.b64decode(match).decode('utf-8', errors='ignore')
                text = text.replace(match, decoded)
                print(f"[⚠️ LAYER 1] Base64 unmasked!")
            except:
                continue

        # 3. Targeted Keyword Neutralization (Dunders & dangerous calls)
        dangerous_keywords = ["__import__", "__subclasses__", "eval(", "exec(", "os.system"]
        for keyword in dangerous_keywords:
            if keyword in text.lower():
                text = text.replace(keyword, f"[RESTRICTED_KEYWORD: {keyword.strip('(')}] ")

        # 4. NEW: Structural Neutralizer (The "No-Delete" HTML Filter)
        # Neutralize START tags: <script> -> [TAG_START: script]
        text = re.sub(r'<([a-zA-Z0-9!]+)([^>]*)>', r' [TAG_START: \1] ', text)
        # Neutralize END tags: </script> -> [TAG_END: script]
        text = re.sub(r'<\/([a-zA-Z0-9]+)>', r' [TAG_END: \1] ', text)

        # 5. Noise Reduction (Clean up any remaining stray brackets)
        # Now we can safely remove any < or > because the "Good" ones are already [TAG_...]
        # text = text.replace("<", " ").replace(">", " ")

        # Group A: Standard (Allowed characters)
        allowed_standard = r'\w\s.,?!:\\'
        allowed_math = r'+=*<>/%\^\-' 
        allowed_code = r'|&()\[\]{}#'
        
        safe_pattern = f'[^{allowed_standard}{allowed_math}{allowed_code}]'
        text = re.sub(safe_pattern, ' ', text)

        # 6. Final Normalization
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text