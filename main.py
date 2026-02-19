from policy_engine import PolicyEngine

def main():
    engine = PolicyEngine("intent_model.yaml", enable_ai_layer=True)

    print("🔐 Two-Layer Instruction Policy Engine")
    print("  Layer 1: Role-based rules")
    print("  Layer 2: AI injection detection")
    print("\nType 'check <id>' to check quarantine status, 'reload' to refresh approved roles, 'exit' to quit.\n")

    while True:
        user_input = input("USER > ").strip()

        if user_input.lower() == "exit":
            break

        # reload approved roles cache (use after admin approves something)
        if user_input.lower() == "reload":
            engine.reload_approved_cache()
            print("ENGINE > ✅ Approved roles cache refreshed.\n")
            print("-" * 60)
            continue

        # user checking status of a previous quarantine
        if user_input.lower().startswith("check "):
            entry_id = user_input.split(" ", 1)[1].strip()
            print("ENGINE >", engine.check_status(entry_id))
            print("-" * 60)
            continue

        decision = engine.evaluate(user_input)

        # Display AI scan results if available
        print("\n" + "="*60)
        if decision.ai_scan:
            ai = decision.ai_scan
            print(f"[LAYER 2 SCAN] {ai['label']} | Confidence: {ai['score']:.2%} | Latency: {ai['latency_seconds']}s")
        else:
            print("[LAYER 2 SCAN] Not available")
        
        print("="*60)

        # Show detailed tier result
        if decision.tier == "quarantine":
            print("TIER RESULT  > QUARANTINE ⚠️")
            print("REASON       >", decision.reason)
            print(f"QUARANTINE ID: {decision.quarantine_id}")
            print(f"               Type 'check {decision.quarantine_id}' to see the decision.")
        elif decision.tier == "pass":
            print("TIER RESULT  > PASS ✅")
            print("REASON       >", decision.reason)
        else:
            print("TIER RESULT  > BLOCK ❌")
            print("REASON       >", decision.reason)

        # Final verdict banner
        print("="*60)
        if decision.allowed:
            print("║ ✅ OVERALL VERDICT: INPUT ACCEPTED - REQUEST PROCESSED     ║")
        else:
            if decision.tier == "quarantine":
                print("║ ⚠️  OVERALL VERDICT: INPUT ON HOLD - AWAITING REVIEW       ║")
            else:
                print("║ ❌ OVERALL VERDICT: INPUT REJECTED - REQUEST DENIED        ║")
        print("="*60 + "\n")

if __name__ == "__main__":
    main()