from policy_engine import PolicyEngine

def main():
    engine = PolicyEngine("intent_model.yaml")

    print("🔐 Instruction Consistency Policy Engine")
    print("Type 'check <id>' to check quarantine status, 'exit' to quit.\n")

    while True:
        user_input = input("USER > ").strip()

        if user_input.lower() == "exit":
            break

        # user checking status of a previous quarantine
        if user_input.lower().startswith("check "):
            entry_id = user_input.split(" ", 1)[1].strip()
            print("ENGINE >", engine.check_status(entry_id))
            print("-" * 50)
            continue

        decision = engine.evaluate(user_input)

        if decision.tier == "quarantine":
            print("ENGINE > QUARANTINE ⚠️")
            print("REASON >", decision.reason)
            print(f"      Your quarantine ID: {decision.quarantine_id}")
            print(f"      Type 'check {decision.quarantine_id}' to see the decision once reviewed.")
        elif decision.tier == "pass":
            print("ENGINE > PASS ✅")
            print("REASON >", decision.reason)
        else:
            print("ENGINE > BLOCK ❌")
            print("REASON >", decision.reason)

        print("-" * 50)

if __name__ == "__main__":
    main()