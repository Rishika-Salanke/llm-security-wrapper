from transformers import pipeline
import time

class InjectionClassifier:
    """
    Layer 2: Semantic Analysis (The AI Guard)
    Responsibility: Detect malicious INTENT (Jailbreaks, Injections).
    """
    def __init__(self):
        print("[⏳ LAYER 2] Loading AI Security Model... (This happens only once)")
        
        # We use a model pre-trained to detect prompt injections
        # Source: ProtectAI (Hugging Face)
        self.classifier = pipeline(
            "text-classification", 
            model="protectai/deberta-v3-base-prompt-injection", 
            device=-1  # Force CPU (Change to 0 if you have a GPU)
        )
        print("[✅ LAYER 2] Model Loaded! Ready to scan.")

    def is_safe(self, text: str) -> dict:
        """
        Scans the text for malicious intent.
        Returns: {'safe': bool, 'score': float, 'label': str}
        """
        start_time = time.time()
        
        # The model returns a list of dicts: [{'label': 'INJECTION', 'score': 0.99}]
        # We take the first result [0]
        result = self.classifier(text)[0]
        
        label = result['label']
        score = result['score']
        
        # LOGIC: If the model is confident it's an injection, BLOCK it.
        # We use a high threshold (0.9) to minimize False Positives.
        is_safe = True
        if label == "INJECTION" and score > 0.9:
            is_safe = False
            
        latency = round(time.time() - start_time, 3)
        
        return {
            "safe": is_safe,
            "score": score,
            "label": label,
            "latency_seconds": latency
        }