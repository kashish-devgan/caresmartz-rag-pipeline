"""
Interactive CLI chatbot for the Hierarchical RAG system.

Requires the FastAPI server to be running:
    uvicorn app.main:app --reload --port 8000

Usage:
    python scripts/chatbot_hrag.py

Commands during session:
    /debug    — toggle retrieval debug info (shows matched parent scores)
    /k <n>    — change top_k_parents (default 3)
    /quit     — exit
"""
import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"
CHAT_URL = f"{BASE_URL}/api/hrag/chat"
STATS_URL = f"{BASE_URL}/api/hrag/admin/stats"

BOLD  = "\033[1m"
GREEN = "\033[92m"
CYAN  = "\033[96m"
GRAY  = "\033[90m"
RED   = "\033[91m"
RESET = "\033[0m"


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def print_stats() -> None:
    try:
        stats = get_json(STATS_URL)
        ns = stats.get("namespaces", {})
        parents_count  = ns.get("hrag_parents",  {}).get("vector_count", 0)
        children_count = ns.get("hrag_children", {}).get("vector_count", 0)
        print(f"{GRAY}Index: {parents_count} parents | {children_count} children{RESET}\n")
    except Exception:
        print(f"{GRAY}(could not fetch index stats){RESET}\n")


def main() -> None:
    print(f"\n{BOLD}CareSmartz360 Hierarchical RAG Chatbot{RESET}")
    print("─" * 42)
    print(f"{GRAY}Server: {BASE_URL}{RESET}")
    print_stats()
    print(f"Commands: {CYAN}/debug{RESET}  {CYAN}/k <n>{RESET}  {CYAN}/quit{RESET}")
    print("─" * 42)

    show_debug = False
    top_k_parents = 3

    while True:
        try:
            user_input = input(f"\n{BOLD}You:{RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            sys.exit(0)

        if not user_input:
            continue

        # --- Commands ---
        if user_input.lower() in ("/quit", "/exit", "/q"):
            print("Bye!")
            sys.exit(0)

        if user_input.lower() == "/debug":
            show_debug = not show_debug
            print(f"{GRAY}Debug mode: {'ON' if show_debug else 'OFF'}{RESET}")
            continue

        if user_input.lower().startswith("/k "):
            try:
                top_k_parents = int(user_input.split()[1])
                print(f"{GRAY}top_k_parents set to {top_k_parents}{RESET}")
            except (IndexError, ValueError):
                print(f"{RED}Usage: /k <number>{RESET}")
            continue

        # --- Chat ---
        payload = {
            "question": user_input,
            "top_k_children": 10,
            "top_k_parents": top_k_parents,
        }

        try:
            result = post_json(CHAT_URL, payload)
        except urllib.error.URLError as exc:
            print(f"{RED}Connection error: {exc}{RESET}")
            print(f"{GRAY}Is the server running? uvicorn app.main:app --reload{RESET}")
            continue
        except Exception as exc:
            print(f"{RED}Error: {exc}{RESET}")
            continue

        # --- Print answer ---
        print(f"\n{GREEN}{BOLD}Assistant:{RESET}")
        print(result.get("answer", "(no answer)"))

        # --- Sources ---
        sources = result.get("sources", [])
        if sources:
            print(f"\n{CYAN}Sources:{RESET}")
            for i, src in enumerate(sources, 1):
                score = src.get("score", 0)
                chunks = src.get("matched_chunks", 1)
                print(
                    f"  {i}. {src.get('title', 'Untitled')} "
                    f"{GRAY}(score={score:.3f}, chunks={chunks}){RESET}"
                )
                if src.get("url"):
                    print(f"     {GRAY}{src['url']}{RESET}")

        # --- Debug info ---
        if show_debug and result.get("retrieval_debug"):
            debug = result["retrieval_debug"]
            print(f"\n{GRAY}[Debug] {json.dumps(debug, indent=2)}{RESET}")

        # --- Images ---
        images = result.get("image_urls", [])
        if images:
            print(f"\n{GRAY}Images: {', '.join(images[:3])}{RESET}")


if __name__ == "__main__":
    main()