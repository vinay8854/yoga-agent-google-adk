"""
agent.py

Local test agent for Nutrition Agent.
Mirrors the exact flow of production's specialists.py → nutrition_agent().
Uses google-genai (new SDK) — same as production.

Flow:
  1. Load skills → build system prompt (same as production's STATIC_AGENT_PROMPTS["nutrition_agent"])
  2. Load user_doc.json → build [CTX] context prefix (same as production's _build_dynamic_context_prefix)
  3. Call Gemini API via google-genai
  4. Parse & return JSON output
"""

import json
import os
import pathlib
import time
from dotenv import dotenv_values

from google import genai
from google.genai import types

# Official Google ADK imports
from google.adk.skills import load_skill_from_dir

# ─── Load env (Reading DIRECTLY from file to ignore machine environment) ──────
dotenv_path = pathlib.Path(__file__).parent / ".env"

def get_config():
    # 1. Try system environment variables first (for Render/Production)
    api_key = os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL")

    # 2. Fallback to local .env file (for Local Development)
    source = "System Environment"
    if not api_key:
        config = dotenv_values(dotenv_path)
        api_key = config.get("GEMINI_API_KEY", "")
        model = config.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
        source = f".env file ({dotenv_path})"

    if model:
        model = model.replace("models/", "")
    else:
        model = "gemini-2.5-flash-lite"
        
    return api_key, model, source

api_key, model, source = get_config()
if not api_key:
    print(f"[agent] ERROR: GEMINI_API_KEY not found!")
    raise RuntimeError(f"GEMINI_API_KEY not set!")

masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "****"
print(f"[agent] Initial Config: Loaded key from {source} ({masked_key})")
print(f"[agent] Initial Config: Using model {model}")






# ─── Shared rules (mirrors production's config/prompts.py) ───────────────────
# ─── Core Rules (Mirrors production's config/prompts.py) ───────────────────

def build_shared_core_prompt() -> str:
    path = pathlib.Path(__file__).parent / "yoga" / "shared_core.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

def build_system_prompt() -> str:
    """
    Helper for the UI to show the full assembled prompt.
    """
    shared_core = build_shared_core_prompt()
    
    skills_base = pathlib.Path(__file__).parent / "yoga"
    skill_blocks = []
    
    if skills_base.exists():
        for skill_dir in sorted(skills_base.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if skill_dir.is_dir() and skill_md.exists():
                try:
                    # Basic extraction for the UI preview
                    raw = skill_md.read_text(encoding="utf-8")
                    if "---" in raw:
                        parts = raw.split("---")
                        body = parts[-1].strip()
                    else:
                        body = raw.strip()
                    skill_blocks.append(f"<skill name=\"{skill_dir.name}\">\n{body}\n</skill>")
                except:
                    pass
    
    skills_instr = "\n\n".join(skill_blocks)
    return f"{shared_core}\n\n# SKILL CAPABILITIES AND SPECIFIC RULES\n{skills_instr}"

# ─── Build [CTX] prefix ───────────────────────────────────────────────────────
def build_context_prefix(user_doc: dict, language: str) -> str:
    pi            = user_doc.get("personal_information", {})
    ps_map        = user_doc.get("personal_summary", {})
    
    # Profile block
    profile_parts = []
    for label, key in [("Name", "name"), ("Location", "location"),
                       ("Health issues", "health_issues"),
                       ("General info", "general_info")]:
        v = pi.get(key, "")
        if v:
            profile_parts.append(f"{label}: {v}")
    personal_info_str = "\n".join(profile_parts) or "(profile not yet collected)"

    # Health context for yoga
    health_str   = (pi.get("health_issues") or "").lower()
    health_notes = []
    if any(k in health_str for k in ["back pain", "slip disc", "sciatica"]):
        health_notes.append("BACK ISSUES: Be very careful with forward bends. Recommend modifications.")
    if any(k in health_str for k in ["knee", "arthritis"]):
        health_notes.append("KNEE ISSUES: No pressure on knees. Use cushions or avoid kneeling poses.")
    if any(k in health_str for k in ["bp", "hypertension"]):
        health_notes.append("HIGH BP: Avoid holding breath (Kumbhaka) and sudden head-down poses.")
    if "pregnancy" in health_str:
        health_notes.append("PREGNANCY: Gentle stretches only. No belly pressure or intense twists.")
    
    health_block = "\n".join(health_notes) if health_notes else "No specific physical restrictions identified yet."

    # Structured KV block
    kv_lines = []
    for k, v in sorted(ps_map.items()):
        if k == "_long_term": continue
        if isinstance(v, str) and v.strip():
            kv_lines.append(f"{k}: {v}")
    kv_block = "\n".join(kv_lines) or "(none)"

    # Language instruction
    if language == "Hinglish":
        lang_block = (
            "- ALWAYS reply in Hinglish — a natural, casual mix of Hindi and English.\n"
            "- Use Hindi for everyday words: 'khana', 'subah', 'thoda', 'bilkul', 'aap'.\n"
            "- Ensure the tone is friendly and conversational."
        )
    else:
        lang_block = "- Reply in clear, professional English."

    return (
        f"[CTX]\n"
        f"[PROFILE]\n{personal_info_str}\n\n"
        f"[HEALTH_RULES]\n{health_block}\n\n"
        f"[PSUM_KV]\n{kv_block}\n\n"
        f"[INSTRUCTIONS]\n{lang_block}\n"
    )


def wrap_query_with_language(query: str, language: str) -> str:
    if language == "Hinglish":
        prefix = "[LANGUAGE: Reply in Hinglish — casual Hindi+English mix. Roman script only.]\n"
    else:
        prefix = "[LANGUAGE: Reply STRICTLY in Indian English. NO Hindi words. Use 'you'/'your'.]\n"
    return prefix + query


# ─── ADK Agent Initialization ───────────────────────────────────────────────

# ─── Main agent call ──────────────────────────────────────────────────────────

def run_yoga_agent(query: str, user_doc: dict, language: str = "Hinglish") -> dict:
    """
    Runs the agent using google-genai (SDK) with ADK-loaded skills.
    """
    api_key, model_id = get_config()
    client = genai.Client(api_key=api_key)
    
    # 1. Load Skills using ADK
    skills_base = pathlib.Path(__file__).parent / "yoga"
    loaded_skills = []
    if skills_base.exists():
        for skill_dir in sorted(skills_base.iterdir()):
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                try:
                    skill = load_skill_from_dir(skill_dir)
                    # Manually load schema.json as ADK loader may ignore it
                    schema_path = skill_dir / "schema.json"
                    if schema_path.exists():
                        skill.resources.assets['schema.json'] = schema_path.read_text(encoding='utf-8')
                    loaded_skills.append(skill)
                except Exception as e:
                    print(f"[agent] Error loading skill {skill_dir.name}: {e}")

    # 2. Build System Prompt (Shared Core + ADK Skill Instructions)
    shared_core = build_shared_core_prompt()
    skill_blocks = []
    for skill in loaded_skills:
        # Wrap instructions in XML-like tags for clarity
        skill_blocks.append(f"<skill name=\"{skill.name}\">\n{skill.instructions}\n</skill>")
    
    system_prompt = f"{shared_core}\n\n# SKILL CAPABILITIES AND SPECIFIC RULES\n" + "\n\n".join(skill_blocks)

    # 3. Dynamic Schema Building
    properties = {
        "reassurance":          types.Schema(type=types.Type.STRING, description="Personalized greeting or reassurance using user's name (e.g., Vinay ji). Max 15 words. REQUIRED."),
        "closing_question":     types.Schema(type=types.Type.STRING, description="A warm, personalized follow-up question wrapped in **double asterisks**. REQUIRED."),
        "memory":               types.Schema(type=types.Type.STRING, description="New facts learned about user."),
        "current_chat_summary": types.Schema(type=types.Type.STRING, description="Compact summary of this turn."),
        "general_info_update":  types.Schema(type=types.Type.STRING, nullable=True),
        "health_issues_update": types.Schema(type=types.Type.STRING, nullable=True),
    }
    required_fields = ["reassurance", "closing_question", "memory", "current_chat_summary", "general_info_update", "health_issues_update"]

    # Parse JSON schemas from ADK skills
    for skill in loaded_skills:
        print(f"[agent] Checking skill: {skill.name}, Assets: {list(skill.resources.assets.keys())}")
        schema_json_str = skill.resources.assets.get('schema.json')
        if schema_json_str:
            try:
                s_data = json.loads(schema_json_str)
                s_props = s_data.get("properties", {})
                for p_name, p_def in s_props.items():
                    if p_name not in properties:
                        p_type = types.Type.STRING
                        items  = None
                        if p_def.get("type") == "array": 
                            p_type = types.Type.ARRAY
                            items = types.Schema(type=types.Type.STRING)
                        elif p_def.get("type") == "object": 
                            p_type = types.Type.OBJECT
                        
                        properties[p_name] = types.Schema(
                            type=p_type,
                            items=items,
                            description=p_def.get("description", ""),
                            nullable=True
                        )
            except Exception as e:
                print(f"[agent] Schema parse error for {skill.name}: {e}")

    # Add general_talk field at the end
    properties["general_talk"] = types.Schema(
        type=types.Type.STRING, 
        description="Greeting or general chat only. Max 10 words. Leave EMPTY if providing yoga advice.",
        nullable=True
    )

    schema = types.Schema(
        type=types.Type.OBJECT,
        properties=properties,
        required=required_fields,
    )

    # 4. Build Context and Contents (Multi-turn)
    ctx_prefix = build_context_prefix(user_doc, language)
    history    = user_doc.get("history", {}).get("personal", [])
    
    contents = []
    for i, turn in enumerate(history[-5:]):
        user_q = (turn.get("user_query") or "").strip()
        agent_a = (turn.get("agent_response") or "").strip()
        if not user_q: continue
        
        user_text = wrap_query_with_language(user_q, language)
        if i == 0: user_text = ctx_prefix + user_text
        
        contents.append(types.Content(role="user", parts=[types.Part(text=user_text)]))
        if agent_a:
            # Past responses as dummy JSON
            agent_json = json.dumps({"general_talk": agent_a, "memory": "", "current_chat_summary": ""})
            contents.append(types.Content(role="model", parts=[types.Part(text=agent_json)]))

    # Current message
    lang_wrap = wrap_query_with_language(query, language)
    current_text = lang_wrap if contents else ctx_prefix + lang_wrap
    contents.append(types.Content(role="user", parts=[types.Part(text=current_text)]))

    # 5. API Call via google-genai
    print(f"[agent] Calling Gemini ({model_id}) for: {query[:50]}...")
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        raw = response.text or "{}"
        data = json.loads(raw)
    except Exception as e:
        print(f"[agent] API/Parse error: {e}")
        data = {"general_talk": str(e), "ok": False}

    # 6. Post-process (Assemble response from fields if empty)
    if not data.get("general_talk"):
        parts = []
        
        # Always add reassurance/greeting at the start
        reassurance = data.get("reassurance")
        if reassurance:
            parts.append(reassurance)

        # Skill-specific fields (exclude base/system fields)
        base_fields = ["general_talk", "memory", "current_chat_summary", "general_info_update", "health_issues_update", "closing_question", "reassurance", "token_usage", "ok", "yoga_end_ack"]
        for field, val in data.items():
            if field not in base_fields and val:
                if isinstance(val, list):
                    parts.append("\n".join(f"- {item}" for item in val))
                else:
                    parts.append(str(val))
        
        # Always add the closing question at the end
        cq = data.get("closing_question")
        if cq:
            parts.append(cq)
            
        if parts: data["response"] = "\n\n".join(parts)
    else:
        # If model put everything in general_talk, use that as the response
        data["response"] = data["general_talk"]
        if data.get("closing_question") and data["closing_question"] not in data["response"]:
            data["response"] += "\n\n" + data["closing_question"]

    # 7. Token Usage (Balanced Breakdown for Dashboard)
    token_usage = {
        "shared_core": 0,
        "skills": 0,
        "skills_breakdown": {},
        "user_msg": 0,
        "thought": 0,
        "history_and_schema": 0,
        "output": 0,
        "total": 0
    }
    
    try:
        # 1. Count individual input components
        token_usage["shared_core"] = client.models.count_tokens(model=model_id, contents=shared_core).total_tokens
        
        if skills_base.exists():
            for skill_dir in sorted(skills_base.iterdir()):
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    try:
                        skill = load_skill_from_dir(skill_dir)
                        st = client.models.count_tokens(model=model_id, contents=skill.instructions).total_tokens
                        token_usage["skills_breakdown"][skill_dir.name] = st
                        token_usage["skills"] += st
                    except:
                        pass
        
        token_usage["user_msg"] = client.models.count_tokens(model=model_id, contents=current_text).total_tokens
        
        # 2. Get ground truth from API response
        if 'response' in locals() and hasattr(response, 'usage_metadata') and response.usage_metadata:
            u = response.usage_metadata
            token_usage["total"] = u.total_token_count
            token_usage["output"] = u.candidates_token_count
            # User requested to limit thought tokens to zero on display
            token_usage["thought"] = 0
            
            # 3. BALANCE THE EQUATION
            # History/Schema = Total - (Manual Input Sum + Output + Thought)
            manual_input_sum = token_usage["shared_core"] + token_usage["skills"] + token_usage["user_msg"]
            other_parts = manual_input_sum + token_usage["output"] + token_usage["thought"]
            
            # The remainder is history context + JSON schema overhead
            token_usage["history_and_schema"] = max(0, token_usage["total"] - other_parts)
            
    except Exception as e:
        print(f"[agent] Token counting error: {e}")

    data["token_usage"] = token_usage

    return data

