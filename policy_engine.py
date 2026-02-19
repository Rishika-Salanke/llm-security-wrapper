import yaml
import re
import json
import uuid
import datetime
from dataclasses import dataclass

import os as _os
LOG_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "quarantine_log.json")

@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    tier: str          # "pass" | "quarantine" | "block"
    quarantine_id: str = None   # only set when tier == "quarantine"

class PolicyEngine:
    def __init__(self, rule_file: str):
        with open(rule_file, "r") as f:
            self.rules = yaml.safe_load(f)

        self.safe_personas   = set(self.rules["personas"]["safe"])
        self.protected_roles = set(self.rules["personas"]["protected"])

        tier2 = self.rules["routing"]["tiers"][1]["response"]
        self.quarantine_msg = tier2["on_quarantine"].strip()
        self.approved_msg   = tier2["on_approved"].strip()
        self.rejected_msg   = tier2["on_rejected"].strip()
        self.expired_msg    = tier2["on_expired"].strip()
        self.block_msg      = self.rules["routing"]["tiers"][2]["response"]
        self.pass_msg       = self.rules["routing"]["tiers"][0]["response"]

    def _normalize(self, text: str) -> str:
        return text.lower().strip()

    def _extract_requested_role(self, text: str):
        match = re.search(
            r"(act as|pretend to be|behave like|roleplay as|pose as|impersonate)\s+(?:a|an|the)?\s*(\w+)",
            text,
            re.I
        )
        if match:
            return match.group(2).lower()
        return None

    def _log_quarantine(self, user_input: str, role: str) -> str:
        """Write quarantined input to log file, return the quarantine ID."""
        entry_id = str(uuid.uuid4())[:8]   # short readable ID
        entry = {
            "id":        entry_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "input":     user_input,
            "role":      role or "unknown",
            "status":    "pending"          # pending | approved | rejected | expired
        }
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry_id

    def check_status(self, entry_id: str) -> str:
        """User calls this to check if their quarantined input was resolved."""
        try:
            with open(LOG_FILE, "r") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if entry["id"] == entry_id:
                        status = entry["status"]
                        if status == "pending":
                            return f"⏳ [{entry_id}] Still under review. Please check back later."
                        elif status == "approved":
                            return f"✅ [{entry_id}] {self.approved_msg}"
                        elif status == "rejected":
                            return f"❌ [{entry_id}] {self.rejected_msg}"
                        elif status == "expired":
                            return f"⏱️  [{entry_id}] {self.expired_msg}"
        except FileNotFoundError:
            pass
        return f"❓ [{entry_id}] ID not found in log."

    def evaluate(self, user_input: str) -> PolicyDecision:
        text = self._normalize(user_input)
        requested_role = self._extract_requested_role(text)

        # 1️⃣ No role mentioned → quarantine
        if not requested_role:
            qid = self._log_quarantine(user_input, None)
            return PolicyDecision(allowed=False, reason=self.quarantine_msg, tier="quarantine", quarantine_id=qid)

        # 2️⃣ Protected role → block
        if requested_role in self.protected_roles:
            return PolicyDecision(allowed=False, reason=self.block_msg, tier="block")

        # 3️⃣ Safe role → pass
        if requested_role in self.safe_personas:
            return PolicyDecision(allowed=True, reason=self.pass_msg, tier="pass")

        # 4️⃣ Unknown role → quarantine
        qid = self._log_quarantine(user_input, requested_role)
        return PolicyDecision(allowed=False, reason=self.quarantine_msg, tier="quarantine", quarantine_id=qid)