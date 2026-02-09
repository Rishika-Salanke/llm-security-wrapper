import ftfy
import base64
import urllib.parse
import re

class InputSanitizer:
    """
    Layer 1: Input Sanitization (Pre-LLM)
    Responsibility: Canonicalization, Encoding detection, and Stripping dangerous tags.
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

        # 4. Smart HTML Strip (Remove <script>, <div>, etc.)
        # Strategy: Only remove if '<' is followed by a letter (a-z) or '/'
        # This preserves mathematical inequalities like "1 < 2"
        text = re.sub(r'<[a-zA-Z\/][^>]*>', '', text)

        # 5. Noise Reduction (Granular Configuration)
        # We isolate risky symbols into groups. This makes it easy to explain 
        # to the team which features are enabled (Math, Code, etc.).
        
        # Group A: Standard English (Letters, Numbers, Spaces, Basic Punctuation)
        allowed_standard = r'\w\s.,?!:'
        
        # Group B: Math Operators (Enabled for Math Queries)
        # Includes: + - * / % = < > ^
        allowed_math = r'+=<>*/%\^\-' 
        
        # Group C: Coding & Logic Symbols (Enabled for Code Queries)
        # Includes: | & ( ) [ ] { } #
        # Added '#' for Python comments and Markdown headers.
        allowed_code = r'|&()\[\]{}#'
        
        # Combine patterns into a single "Safe List"
        # Any character NOT in this list will be replaced with a space.
        safe_pattern = f'[^{allowed_standard}{allowed_math}{allowed_code}]'
        
        text = re.sub(safe_pattern, ' ', text)

        # 6. Normalize Whitespace (Collapse "  " into " ")
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text