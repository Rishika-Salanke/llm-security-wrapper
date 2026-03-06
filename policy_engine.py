import yaml
import re
import json
import uuid
import datetime
import os as _os
from dataclasses import dataclass

LOG_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "quarantine_log.json")

@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    tier: str          # "pass" | "quarantine" | "block"
    quarantine_id: str = None   # only set when tier == "quarantine"
    ai_scan: dict = None        # Layer 2 results if run

class PolicyEngine:
    def __init__(self, rule_file: str, enable_ai_layer: bool = True):
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

        # Cache of previously approved roles (loaded from log)
        self._approved_roles_cache = self._load_approved_roles()

        # Layer 2 AI Guard (optional)
        self.ai_guard = None
        if enable_ai_layer:
            try:
                from injection_classifier import InjectionClassifier
                self.ai_guard = InjectionClassifier()
            except Exception as e:
                print(f"[⚠️  LAYER 2] Could not load AI model: {e}")
                print("[ℹ️  LAYER 2] Continuing with Layer 1 (role-based) only.")

    def _load_approved_roles(self) -> set:
        """Load all previously approved roles from log into memory cache."""
        approved = set()
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    entry = json.loads(line.strip())
                    if entry.get("status") == "approved" and entry.get("role"):
                        approved.add(entry["role"])
        except FileNotFoundError:
            pass
        return approved

    def _is_role_approved(self, role: str) -> bool:
        """Check if this role was previously approved (cached lookup)."""
        return role in self._approved_roles_cache

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
        entry_id = str(uuid.uuid4())[:8]
        entry = {
            "id":        entry_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "input":     user_input,
            "role":      role or "unknown",
            "status":    "pending"
        }
        
        try:
            log_dir = _os.path.dirname(LOG_FILE)
            if log_dir and not _os.path.exists(log_dir):
                _os.makedirs(log_dir)
            
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
                f.flush()
                _os.fsync(f.fileno())
            
            print(f"[✓] Quarantine logged: ID={entry_id}, Role={role or 'none'}")
        except Exception as e:
            print(f"[✗] Failed to log quarantine: {e}")
        
        return entry_id

    def check_status(self, entry_id: str) -> str:
        """User calls this to check if their quarantined input was resolved."""
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
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
        except Exception as e:
            print(f"[✗] Error reading log: {e}")
        return f"❓ [{entry_id}] ID not found in log."

    def reload_approved_cache(self):
        """Refresh the approved roles cache from log file."""
        self._approved_roles_cache = self._load_approved_roles()

    def evaluate(self, user_input: str) -> PolicyDecision:
        """
        Two-layer security evaluation with hybrid logic + approved role caching.
        """
        
        text = self._normalize(user_input)
        requested_role = self._extract_requested_role(text)
        is_role_based = requested_role is not None
        
        # ═══════════════════════════════════════════════════════════════
        # LAYER 2: AI Semantic Scan
        # ═══════════════════════════════════════════════════════════════
        ai_result = None
        if self.ai_guard:
            ai_result = self.ai_guard.is_safe(user_input)
        
        # ═══════════════════════════════════════════════════════════════
        # DECISION LOGIC
        # ═══════════════════════════════════════════════════════════════
        
        if is_role_based:
            # ──────────────────────────────────────────────────────────
            # ROLE-BASED INPUT: Layer 1 decides, Layer 2 can block
            # ──────────────────────────────────────────────────────────
            
            # Layer 2 override: if AI detects injection, block immediately
            if ai_result and not ai_result["safe"]:
                return PolicyDecision(
                    allowed=False,
                    reason=f"🛡️ AI Guard blocked role request: {ai_result['label']} (confidence: {ai_result['score']:.2%})",
                    tier="block",
                    ai_scan=ai_result
                )
            
            # Layer 1: Role-based policy
            if requested_role in self.protected_roles:
                return PolicyDecision(
                    allowed=False, 
                    reason=self.block_msg, 
                    tier="block",
                    ai_scan=ai_result
                )
            
            if requested_role in self.safe_personas:
                return PolicyDecision(
                    allowed=True, 
                    reason=self.pass_msg, 
                    tier="pass",
                    ai_scan=ai_result
                )
            
            # CHECK CACHE: Was this role previously approved?
            if self._is_role_approved(requested_role):
                return PolicyDecision(
                    allowed=True,
                    reason=f"Role '{requested_role}' was previously approved.",
                    tier="pass",
                    ai_scan=ai_result
                )
            
            # Unknown role → quarantine
            qid = self._log_quarantine(user_input, requested_role)
            return PolicyDecision(
                allowed=False, 
                reason=self.quarantine_msg, 
                tier="quarantine", 
                quarantine_id=qid,
                ai_scan=ai_result
            )
        
        else:
            # ──────────────────────────────────────────────────────────
            # NON-ROLE-BASED INPUT: Layer 2 decides entirely
            # ──────────────────────────────────────────────────────────
            
            if ai_result:
                if not ai_result["safe"]:
                    return PolicyDecision(
                        allowed=False,
                        reason=f"🛡️ AI Guard blocked: {ai_result['label']} (confidence: {ai_result['score']:.2%})",
                        tier="block",
                        ai_scan=ai_result
                    )
                else:
                    return PolicyDecision(
                        allowed=True,
                        reason="AI Guard: Input is safe.",
                        tier="pass",
                        ai_scan=ai_result
                    )
            else:
                qid = self._log_quarantine(user_input, None)
                return PolicyDecision(
                    allowed=False, 
                    reason=self.quarantine_msg, 
                    tier="quarantine", 
                    quarantine_id=qid,
                    ai_scan=ai_result
                )