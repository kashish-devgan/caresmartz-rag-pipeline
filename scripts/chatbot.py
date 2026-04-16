import sys
import os
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

API_URL = "http://127.0.0.1:8000/api/chat"

BANNER = """
======================================================
   CareSmartz360 RAG Chatbot
   Type your question and press Enter.
   Type 'quit' or 'exit' to stop.
   Type 'clear' to clear the screen.
======================================================
"""

def ask(question: str, top_k: int = 3) -> None:
    try:
        response = requests.post(
            API_URL,
            json={"question": question, "top_k": top_k},
            timeout=30,
        )
        if response.status_code != 200:
            print(f"\n[ERROR] API returned {response.status_code}: {response.text}\n")
            return

        data = response.json()

        print("\n" + "─" * 54)
        print("ANSWER:")
        print("─" * 54)
        print(data["answer"])

        if data.get("sources"):
            print("\nSOURCES:")
            for i, src in enumerate(data["sources"], 1):
                print(f"  {i}. {src['title']}")
                print(f"     {src['url']}  (score: {src['score']})")

        if data.get("image_urls"):
            print("\nRELATED IMAGES:")
            for url in data["image_urls"]:
                print(f"  - {url}")
            article_id = data["sources"][0]["url"].split("/")[-1] if data.get("sources") else ""
            if article_id:
                print(f"\n  View gallery: http://127.0.0.1:8000/api/admin/images/{article_id}/gallery")

        print("─" * 54 + "\n")

    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot connect to the API server.")
        print("Make sure the server is running:")
        print("  uvicorn app.main:app --reload --port 8000\n")
    except requests.exceptions.Timeout:
        print("\n[ERROR] Request timed out. The server may be busy.\n")
    except Exception as exc:
        print(f"\n[ERROR] Unexpected error: {exc}\n")


def main():
    print(BANNER)

    while True:
        try:
            question = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye!\n")
            break

        if not question:
            continue

        if question.lower() in ("quit", "exit", "q"):
            print("\nGoodbye!\n")
            break

        if question.lower() == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            print(BANNER)
            continue

        ask(question)


if __name__ == "__main__":
    main()
