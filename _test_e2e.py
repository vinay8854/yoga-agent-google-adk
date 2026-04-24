import sys, pathlib, json

BASE = pathlib.Path(__file__).parent
sys.path.insert(0, str(BASE))

from agent import run_yoga_agent, build_system_prompt, get_config

# Get current config
api_key, model = get_config()
masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "****"

print(f"Model : {model}")
print(f"Key   : {masked_key}")
print("Skills test...")
prompt = build_system_prompt()
print(f"Prompt: {len(prompt)} chars - OK")

print("\nSending test query...")
user_doc_path = BASE / "user_doc.json"
user_doc = json.load(open(user_doc_path, encoding='utf-8'))
result = run_yoga_agent("hello, suggest me some yoga poses for back pain?", user_doc, "Hinglish")

print("\n--- FULL OUTPUT ---")
print(json.dumps(result, indent=2))
print("\n--- RESPONSE ---")
print(result.get("response", ""))
print("\n--- MEMORY ---")
print(result.get("memory", "(none)"))
print("\n--- SUMMARY ---")
print(result.get("current_chat_summary", ""))
print("\nSUCCESS!")
