import yaml
import re
from dataclasses import dataclass

@dataclass
class PolicyDecision:
    allowed: bool
    reason: str

class PolicyEngine:
    def __init__(self, rule_file: str):
        with open(rule_file, "r") as f:
            self.rules = yaml.safe_load(f)

        self.safe_personas = set(self.rules["personas"]["safe"])
        self.protected_roles = set(self.rules["personas"]["protected"])

    def _normalize(self, text: str) -> str:
        return text.lower().strip()

    def _matches_allowed(self, text: str) -> bool:
        for pattern in self.rules.get("allowed_patterns", []):
            if re.search(pattern, text):
                return True
        return False

    def _extract_requested_role(self, text: str):
        match = re.search(
            r"(act as|pretend to be|be a|behave like)\s+(\w+)",
            text,
            re.I
        )
        if match:
            return match.group(2).lower()
        return None

    def _detect_intent(self, text: str):
        signals = self.rules.get("intent_signals", {})
        for intent, config in signals.items():
            for verb in config.get("verbs", []):
                for target in config.get("targets", []):
                    if verb in text and target in text:
                        return intent
        return None

    def evaluate(self, user_input: str) -> PolicyDecision:
        text = self._normalize(user_input)

        # 1️⃣ Role / persona handling
        requested_role = self._extract_requested_role(text)

        if requested_role:
            if requested_role in self.protected_roles:
                return PolicyDecision(
                    allowed=False,
                    reason=f"Protected role '{requested_role}' cannot be assumed"
                )

            if requested_role in self.safe_personas:
                return PolicyDecision(
                    allowed=True,
                    reason=f"Safe persona '{requested_role}' allowed"
                )

        # 2️⃣ Intent detection
        intent = self._detect_intent(text)
        if intent and intent in self.rules["intent_model"]["forbidden_intents"]:
            return PolicyDecision(
                allowed=False,
                reason=f"Forbidden intent detected: {intent}"
            )

        # 3️⃣ Normal allowed queries
        if self._matches_allowed(text):
            return PolicyDecision(
                allowed=True,
                reason="Allowed informational request"
            )

        # 4️⃣ Default safe pass
        return PolicyDecision(
            allowed=True,
            reason="No policy violation detected"
        )