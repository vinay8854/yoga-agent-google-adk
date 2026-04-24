"""
server.py — Flask backend for the local Agent Test UI

Run: python server.py
Then open: http://localhost:5000
"""

import json
import pathlib
import sys
import os
from flask import Flask, request, jsonify, send_from_directory

# ── Add test_area to path so we can import agent.py ──────────────────────────
BASE = pathlib.Path(__file__).parent
sys.path.insert(0, str(BASE))

from agent import run_yoga_agent, build_system_prompt, build_context_prefix, build_shared_core_prompt

app = Flask(__name__, static_folder=str(BASE / "ui"), static_url_path="")

USER_DOC_PATH = BASE / "user_doc.json"


def load_user_doc() -> dict:
    with open(USER_DOC_PATH, encoding="utf-8") as f:
        return json.load(f)


@app.route("/")
def index():
    return send_from_directory(str(BASE / "ui"), "index.html")


@app.route("/api/user", methods=["GET"])
def get_user():
    """Returns the current user_doc.json contents."""
    try:
        user_doc = load_user_doc()
        return jsonify({"ok": True, "user_doc": user_doc})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/user", methods=["POST"])
def save_user():
    """Saves updated user_doc.json from the UI."""
    try:
        data = request.get_json()
        with open(USER_DOC_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/prompt", methods=["GET"])
def get_prompt():
    """
    Helper for the UI to show the full assembled prompt.
    """
    try:
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
        prompt = f"{shared_core}\n\n# SKILL CAPABILITIES AND SPECIFIC RULES\n{skills_instr}"
        return jsonify({"ok": True, "prompt": prompt})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/skills", methods=["GET"])
def get_skills():
    """Returns list of loaded skills."""
    try:
        skills_base = pathlib.Path(__file__).parent / "yoga"
        skills = []
        if skills_base.exists():
            for d in sorted(skills_base.iterdir()):
                if d.is_dir() and (d / "SKILL.md").exists():
                    skills.append({"name": d.name, "description": "ADK Skill"})
        return jsonify({"ok": True, "skills": skills})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint.
    Body: { query: str, language: "Hinglish" | "English" }
    Returns full agent output + ctx_preview for the debug panel.
    """
    try:
        body     = request.get_json()
        query    = (body.get("query") or "").strip()
        language = (body.get("language") or "Hinglish").strip()

        if not query:
            return jsonify({"ok": False, "error": "query is empty"}), 400

        user_doc    = load_user_doc()
        ctx_preview = build_context_prefix(user_doc, language)

        result = run_yoga_agent(
            query=query,
            user_doc=user_doc,
            language=language,
        )

        # ── Update history and rolling_summaries ─────────────────────────────
        new_turn = {
            "user_query": query,
            "agent_response": result.get("response", "")
        }
        
        # history (full history) - CAPPED AT 5
        if "history" not in user_doc: user_doc["history"] = {}
        if "personal" not in user_doc["history"]: user_doc["history"]["personal"] = []
        user_doc["history"]["personal"].append(new_turn)
        user_doc["history"]["personal"] = user_doc["history"]["personal"][-5:]

        # rolling_summaries (last N turns) - CAPPED AT 5
        if "rolling_summaries" not in user_doc: user_doc["rolling_summaries"] = {}
        if "personal" not in user_doc["rolling_summaries"]: user_doc["rolling_summaries"]["personal"] = []
        
        rolling_turn = {
            "agent_used": "yoga_agent",
            "user_query": query,
            "agent_response": result.get("response", ""),
            "current_chat_summary": result.get("current_chat_summary", "")
        }
        user_doc["rolling_summaries"]["personal"].append(rolling_turn)
        user_doc["rolling_summaries"]["personal"] = user_doc["rolling_summaries"]["personal"][-5:]

        # Save back to file
        try:
            with open(USER_DOC_PATH, "w", encoding="utf-8") as f:
                json.dump(user_doc, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[server] Warning: Failed to save user_doc.json: {e}")

        result["ctx_preview"] = ctx_preview
        result["ok"] = True
        return jsonify(result)

    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("\n" + "=" * 60)
    print("  Yoga Agent Test UI")
    print(f"  Running on port: {port}")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=port)
