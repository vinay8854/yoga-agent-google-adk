"""
run_test.py  —  Test Runner for the local Nutrition Agent

HOW TO USE:
  1. Fill in your GEMINI_API_KEY in test_area/.env
  2. Edit user_doc.json to change the simulated user profile
  3. Run:  python run_test.py
  4. Type your message and press Enter
  5. Type 'q' to quit

LANGUAGE:
  Set LANGUAGE = "Hinglish" or "English" below to test both modes.

WHAT YOU SEE:
  ┌─ SYSTEM PROMPT  : Full assembled prompt (skills + rules)
  ┌─ [CTX] BLOCK    : What the agent "sees" as user context
  ┌─ RESPONSE       : The agent's reply to the user
  ┌─ MEMORY         : Structured facts the agent wants to save
  ┌─ CHAT SUMMARY   : The ≤45-word rolling summary for this turn
  ┌─ PROFILE UPDATES: general_info_update + health_issues_update
"""

import json
import pathlib
import textwrap
import sys
from agent import run_nutrition_agent, build_system_prompt, build_context_prefix

# ─── CONFIG ──────────────────────────────────────────────────────────────────
USER_DOC_PATH = pathlib.Path(__file__).parent / "user_doc.json"

# Set this to "Hinglish" or "English"
LANGUAGE = "Hinglish"

# Set to True to print the full assembled system prompt on startup
SHOW_SYSTEM_PROMPT = False

# Set to True to print the raw JSON output from the LLM
SHOW_RAW_JSON = False
# ─────────────────────────────────────────────────────────────────────────────


def _divider(title: str = "", char: str = "─", width: int = 70) -> str:
    if title:
        pad = max(0, width - len(title) - 4)
        return f"\n{char*2} {title} {char*pad}"
    return char * width


def _wrap(text: str, indent: int = 4) -> str:
    prefix = " " * indent
    return textwrap.fill(text, width=80, initial_indent=prefix, subsequent_indent=prefix)


def load_user_doc() -> dict:
    if not USER_DOC_PATH.exists():
        print(f"❌ user_doc.json not found at {USER_DOC_PATH}")
        sys.exit(1)
    with open(USER_DOC_PATH, encoding="utf-8") as f:
        return json.load(f)


def print_result(result: dict) -> None:
    response            = result.get("response", "")
    memory              = result.get("memory", "")
    chat_summary        = result.get("current_chat_summary", "")
    general_info_update = result.get("general_info_update")
    health_issues_update = result.get("health_issues_update")

    print(_divider("[RESPONSE]"))
    # Print response respecting embedded \n\n for WhatsApp formatting
    for line in response.replace("\\n\\n", "\n\n").replace("\\n", "\n").split("\n"):
        print(f"    {line}")

    print(_divider("[MEMORY - facts to save]"))
    print(_wrap(memory or "(nothing new to save)"))

    print(_divider("[CHAT SUMMARY]"))
    print(_wrap(chat_summary or "(empty)"))

    if general_info_update:
        print(_divider("[GENERAL INFO UPDATE]"))
        print(_wrap(general_info_update))

    if health_issues_update:
        print(_divider("[HEALTH ISSUES UPDATE]"))
        print(_wrap(health_issues_update))

    print(_divider())


def main():
    print("\n" + "=" * 70)
    print("  HABUILD NUTRITION AGENT -- LOCAL TEST")
    print("=" * 70)

    user_doc = load_user_doc()
    pi = user_doc.get("personal_information", {})
    print(f"  User    : {pi.get('name', 'Unknown')} ({pi.get('location', '')})")
    print(f"  Health  : {pi.get('health_issues', 'None')}")
    print(f"  Diet    : {pi.get('dietary_pref', 'Vegetarian')}")
    print(f"  Language: {LANGUAGE}")
    print(f"  Model   : (set in .env)")
    print("=" * 70)

    if SHOW_SYSTEM_PROMPT:
        print(_divider("[SYSTEM PROMPT]"))
        prompt = build_system_prompt()
        print(prompt)
        print(_divider())

    print("\nType your message and press Enter. Type 'q' to quit.\n")

    while True:
        try:
            query = input("  You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! 👋")
            break

        if query.lower() in {"q", "quit", "exit"}:
            print("Goodbye! 👋")
            break

        if not query:
            continue

        print(_divider("[CTX BLOCK SENT TO LLM]"))
        ctx = build_context_prefix(user_doc, LANGUAGE)
        # Print first 800 chars of ctx to keep terminal readable
        preview = ctx[:800] + ("..." if len(ctx) > 800 else "")
        for line in preview.split("\n"):
            print(f"    {line}")

        try:
            result = run_nutrition_agent(
                query=query,
                user_doc=user_doc,
                language=LANGUAGE,
            )
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue

        if SHOW_RAW_JSON:
            print(_divider("[RAW JSON OUTPUT]"))
            print(json.dumps(result, indent=2, ensure_ascii=False))

        print_result(result)


if __name__ == "__main__":
    main()
