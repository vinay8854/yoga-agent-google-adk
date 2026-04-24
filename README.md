# 🧪 Habuild Agent — Local Test Area

Test your agent skills locally **without** Firestore, Vertex AI, or any cloud dependency.
Uses plain Gemini API (Google AI Studio key).

---

## Folder Structure

```
test_area/
├── .env                          ← Your Gemini API key goes here
├── user_doc.json                 ← Mock user profile (replaces Firestore)
├── agent.py                      ← Core agent logic (mirrors specialists.py)
├── skill_loader.py               ← Reads SKILL.md files (mirrors ADKSkillManager)
├── run_test.py                   ← Interactive test runner
├── requirements.txt              ← 2 packages only
└── skills/
    └── nutrition/
        ├── shared_core.md                    ← Agent persona + base rules
        ├── health/SKILL.md                   ← Health conditions skill
        ├── nutrition-skill-info/SKILL.md     ← Nutritional facts skill
        ├── nutrition-skill-swap/SKILL.md     ← Food swap skill
        └── nutrition-skill-guilt/SKILL.md    ← Guilt/shame skill
```

---

## Quick Start

### Step 1 — Install dependencies
```bash
cd test_area
pip install -r requirements.txt
```

### Step 2 — Add your API key
Edit `.env`:
```
GEMINI_API_KEY=AIza...your_key_here
GEMINI_MODEL=gemini-2.0-flash
```
Get your free key at: https://aistudio.google.com/app/apikey

### Step 3 — Run
```bash
python run_test.py
```

---

## What to test

| Query | Skill triggered |
|---|---|
| `is oats good for me?` | `nutrition-skill-info` |
| `yaar maine bahut pizza khaa liya aaj` | `nutrition-skill-guilt` |
| `maida ki jagah kya use karein?` | `nutrition-skill-swap` |
| `I have acidity, what should I eat?` | `health` |

---

## Customise the user

Edit `user_doc.json` to simulate different users:

```json
"personal_information": {
  "name":         "Anita",
  "health_issues":"diabetes",
  "dietary_pref": "Vegetarian"
},
"personal_summary": {
  "wake_time":    "5:30 AM",
  "favourite_foods": "Upma, Dosa"
}
```

---

## Change language mode

In `run_test.py`, change line:
```python
LANGUAGE = "Hinglish"   # or "English"
```

---

## Debug flags (in run_test.py)

| Flag | Default | What it shows |
|---|---|---|
| `SHOW_SYSTEM_PROMPT` | `False` | Full assembled system prompt with all skills |
| `SHOW_RAW_JSON` | `False` | Raw JSON output from the LLM before parsing |

---

## How it mirrors production

| Production (`specialists.py`) | Test Area |
|---|---|
| `STATIC_AGENT_PROMPTS["nutrition_agent"]` | `agent.py → build_system_prompt()` |
| `ADKSkillManager.get_full_instructions()` | `skill_loader.py → SkillManager.get_full_instructions()` |
| `_build_dynamic_context_prefix()` | `agent.py → build_context_prefix()` |
| `_wrap_query_with_language()` | `agent.py → wrap_query_with_language()` |
| Firestore user doc | `user_doc.json` |
| Vertex AI Gemini client | `google-generativeai` with API key |
