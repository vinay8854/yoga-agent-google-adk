"""
skill_loader.py

Lightweight local replacement for the production ADKSkillManager.
No Google ADK dependency required — just reads SKILL.md files from disk.

Usage:
    from skill_loader import SkillManager
    mgr = SkillManager("nutrition")
    full_prompt = mgr.get_full_instructions()
"""

import pathlib


class SkillManager:
    """
    Mimics ADKSkillManager from production's agents/skills/manager.py.
    Reads shared_core.md + all SKILL.md files from a local skills/<domain>/ folder.
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.base_path = pathlib.Path(__file__).parent / domain
        self.shared_core = self._load_shared_core()
        self.skills = self._load_skills()

    def _load_shared_core(self) -> str:
        core_path = self.base_path / "shared_core.md"
        if core_path.exists():
            return core_path.read_text(encoding="utf-8")
        return ""

    def _load_skills(self) -> list[dict]:
        """
        Scans each subdirectory for SKILL.md.
        Returns a list of dicts: { "name": str, "description": str, "instructions": str }
        """
        skills = []
        if not self.base_path.exists():
            print(f"[SkillManager] WARN: skills path not found: {self.base_path}")
            return skills

        for skill_dir in sorted(self.base_path.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if skill_dir.is_dir() and skill_md.exists():
                raw = skill_md.read_text(encoding="utf-8")
                # Parse metadata and schema
                metadata = {}
                schema_data = None
                
                name = skill_dir.name
                description = ""
                lines = raw.splitlines()
                in_frontmatter = False
                body_lines = []
                
                import yaml
                try:
                    # Find frontmatter block
                    if lines[0].strip() == "---":
                        fm_lines = []
                        i = 1
                        while i < len(lines) and lines[i].strip() != "---":
                            fm_lines.append(lines[i])
                            i += 1
                        fm_text = "\n".join(fm_lines)
                        fm_data = yaml.safe_load(fm_text)
                        if fm_data:
                            name = fm_data.get("name", name)
                            description = fm_data.get("description", "")
                            metadata = fm_data.get("metadata", {})
                        
                        # Instructions start after the second ---
                        body_lines = lines[i+1:]
                    else:
                        body_lines = lines
                except Exception as e:
                    print(f"  [SkillManager] Error parsing frontmatter for {name}: {e}")
                    body_lines = lines

                # Load schema if specified in metadata
                schema_path_str = metadata.get("output_schema")
                if schema_path_str:
                    import json
                    schema_path = skill_dir / schema_path_str
                    if schema_path.exists():
                        try:
                            schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
                            print(f"  [SkillManager] Loaded schema for: {name}")
                        except Exception as e:
                            print(f"  [SkillManager] Error loading schema for {name}: {e}")

                instructions = "\n".join(body_lines).strip()
                skills.append({
                    "name": name,
                    "description": description,
                    "instructions": instructions,
                    "schema": schema_data
                })
                print(f"  [SkillManager] Loaded: {name}")
        return skills

    def get_full_instructions(self) -> str:
        """
        Stitches shared_core + ALL skills into one unified system prompt string.
        """
        skill_blocks = []
        for skill in self.skills:
            block = f"<skill name=\"{skill['name']}\">\n{skill['instructions']}\n</skill>"
            skill_blocks.append(block)

        skills_section = "\n\n".join(skill_blocks)
        return f"{self.shared_core}\n\n# SKILL CAPABILITIES AND SPECIFIC RULES\n{skills_section}"
