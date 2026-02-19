import json
import sys
import time

import os as _os
LOG_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "quarantine_log.json")

def load_entries():
    entries = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        print(f"[WARNING] Skipping malformed line: {line[:50]}")
    except FileNotFoundError:
        print("No log file found. No quarantined entries yet.")
        sys.exit(0)
    return entries

def save_entries(entries):
    """Save ALL entries back to the log file (not just pending ones)."""
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
            f.flush()
            _os.fsync(f.fileno())
    except Exception as e:
        print(f"[ERROR] Failed to save entries: {e}")

def list_pending(entries):
    pending = [e for e in entries if e["status"] == "pending"]
    if not pending:
        print("✅ No pending quarantine entries.")
        return
    print(f"\n{'─'*75}")
    print(f"  {'ID':<10} {'ROLE':<20} {'STATUS':<10} INPUT")
    print(f"{'─'*75}")
    for e in pending:
        role = e.get('role', 'N/A')
        preview = e["input"][:35] + "..." if len(e["input"]) > 35 else e["input"]
        print(f"  {e['id']:<10} {role:<20} {e['status']:<10} {preview}")
    print(f"{'─'*75}\n")

def review(entries):
    pending = [e for e in entries if e["status"] == "pending"]
    if not pending:
        print("✅ No pending entries to review.")
        return entries

    for e in pending:
        print(f"\n📋 ID       : {e['id']}")
        print(f"   Role     : {e.get('role', 'N/A')}")
        print(f"   Time     : {e['timestamp']}")
        print(f"   Input    : {e['input']}")
        print(f"   Decision : [a] approve  [r] reject  [s] skip")
        choice = input("   > ").strip().lower()

        if choice == "a":
            e["status"] = "approved"
            print(f"   ✅ Approved [{e['id']}]")
        elif choice == "r":
            e["status"] = "rejected"
            print(f"   ❌ Rejected [{e['id']}]")
        else:
            print(f"   ⏭️  Skipped [{e['id']}]")

    return entries

def main():
    print("\n🔐 Admin Quarantine Review Panel")
    print("Commands: list | review | exit\n")

    while True:
        cmd = input("ADMIN > ").strip().lower()

        if cmd == "exit":
            break
        elif cmd == "list":
            entries = load_entries()
            list_pending(entries)
        elif cmd == "review":
            entries = load_entries()
            updated = review(entries)
            save_entries(updated)
            print("\n💾 Decisions saved to log.\n")
        else:
            print("Unknown command. Use: list | review | exit")

if __name__ == "__main__":
    main()