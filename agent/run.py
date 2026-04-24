import argparse
import asyncio

from dotenv import load_dotenv


def main():
    parser = argparse.ArgumentParser(description="PydanticAI deep-research agent.")
    parser.add_argument("question", nargs="+", help="Question to ask the agent.")
    args = parser.parse_args()

    load_dotenv()
    question = " ".join(args.question)

    from shared.observability import setup_phoenix
    setup_phoenix()

    from agent import run_agent
    result = asyncio.run(run_agent(question))

    print("\n=== ANSWER ===")
    print(result.answer)
    print(f"\nConfidence: {result.confidence}")
    print(f"Citations: {len(result.citations)}")


if __name__ == "__main__":
    main()
