"""
test_agent.py
==============
A simple verification script to test the self-correcting SQL Agent.
"""

import json
from app.agent import SQLAgent


def test():
    # Instantiate agent
    agent = SQLAgent(max_retries=3)

    # Test Question
    question = "How many shipped orders are from USA customers?"

    print("=" * 80)
    print(f"Running Agent with Question: '{question}'")
    print("=" * 80)

    response = agent.run(question)

    print("\n" + "=" * 80)
    print("Agent Execution Completed. Final Response:")
    print("=" * 80)
    print(json.dumps(response, indent=2))
    print("=" * 80)


if __name__ == "__main__":
    test()
