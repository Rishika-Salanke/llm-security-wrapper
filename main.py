from policy_engine import PolicyEngine

def main():
    engine = PolicyEngine("rules.yaml")

    print("🔐 Instruction Consistency Policy Engine")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("USER > ")
        if user_input.lower() == "exit":
            break

        decision = engine.evaluate(user_input)

        print("ENGINE >", "PASS ✅" if decision.allowed else "BLOCK ❌")
        print("REASON >", decision.reason)
        print("-" * 50)

if __name__ == "__main__":
    main()