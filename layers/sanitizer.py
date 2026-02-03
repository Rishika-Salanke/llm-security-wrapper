import ftfy
import base64
import urllib.parse
import re

class InputSanitizer:
    """
    Layer 1: Input Sanitization (Pre-LLM)
    Responsibility: Canonicalization, Encoding detection, and Stripping dangerous tags.
    References: Project Plan [cite: 4, 10, 25]
    """
    
    def sanitize(self, text: str) -> str:
        # 1. Canonicalization (Fix broken unicode/mojibake) 
        # This prevents attackers from using invisible characters to bypass filters.
        text = ftfy.fix_text(text)
        
        # 2. Decode URL Encoding (e.g., %20 -> space) 
        text = urllib.parse.unquote(text)
        
        # 3. Base64 Detection & Decoding 
        # Attackers often hide instructions in Base64. We detect and reveal them.
        if re.match(r'^[A-Za-z0-9+/]+={0,2}$', text) and len(text) > 8:
            try:
                decoded = base64.b64decode(text).decode('utf-8')
                text = f"{text} (Decoded: {decoded})"
                print(f"[⚠️ LAYER 1] Base64 payload detected and decoded!")
            except:
                pass # Not valid Base64, ignore.

        # 4. Deterministic Clean (Remove HTML/Scripts) 
        # Standard cleaning to prevent script injection.
        text = re.sub(r'<[^>]*>', '', text)

        # 5. Remove non-standard characters (Keep only letters, numbers, and basic punctuation)
        # This removes #, %, *, ), etc.
        text = re.sub(r'[^\w\s.,?!-]', ' ', text)

        # 6. Normalize Whitespace (Collapse "  " into " ")
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text