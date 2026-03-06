class ContextManager:
    """
    Layer 3: Context Reinforcement (Instruction Anchoring)
    Responsibility: Anchoring immutable safety rules to every prompt.
    """
    def __init__(self):
        # Model-Friendly Anchor: Uses positive framing to prevent hallucinated refusals
        # We avoid triggering words like "hack" or "illegal" so the LLM stays calm.
        self.system_anchor = (
            "<system_instructions>\n"
            "You are a helpful, professional, and harmless AI assistant.\n"
            "Your primary task is to answer the user's request accurately and directly.\n"
            "Always maintain a polite tone, stick to facts, and prioritize safety.\n"
            "</system_instructions>"
        )

    def reinforce(self, clean_prompt: str) -> str:
        """
        Wraps the user's prompt inside the immutable system rules using clear boundaries.
        """
        # Using clear XML-style delimiters helps small models separate instructions from user text.
        reinforced_text = (
            f"{self.system_anchor}\n\n"
            f"<user_input>\n"
            f"{clean_prompt}\n"
            f"</user_input>"
        )
        
        return reinforced_text