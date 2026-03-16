"""Contract tests for plugin structure.

Verifies:
- plugin.json is valid JSON with required fields
- Version matches across plugin.json and pyproject.toml
- All skill directories have a SKILL.md
- Hooks file is valid JSON
"""

import json
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TestPluginJson:
    @pytest.fixture(autouse=True)
    def load_plugin(self):
        self.path = PROJECT_ROOT / ".claude-plugin" / "plugin.json"
        assert self.path.exists(), "plugin.json not found"
        self.data = json.loads(self.path.read_text())

    def test_is_valid_json(self):
        # If we got here, JSON parsed successfully
        assert isinstance(self.data, dict)

    def test_has_name(self):
        assert "name" in self.data
        assert isinstance(self.data["name"], str)

    def test_has_version(self):
        assert "version" in self.data
        assert re.match(r"\d+\.\d+\.\d+", self.data["version"]), (
            f"Version '{self.data['version']}' doesn't match semver pattern"
        )

    def test_has_description(self):
        assert "description" in self.data
        assert len(self.data["description"]) > 0


class TestVersionConsistency:
    def test_plugin_version_matches_pyproject(self):
        plugin_path = PROJECT_ROOT / ".claude-plugin" / "plugin.json"
        pyproject_path = PROJECT_ROOT / "pyproject.toml"

        plugin_data = json.loads(plugin_path.read_text())
        plugin_version = plugin_data["version"]

        pyproject_text = pyproject_path.read_text()
        match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)
        assert match, "Could not find version in pyproject.toml"
        pyproject_version = match.group(1)

        assert plugin_version == pyproject_version, (
            f"Version mismatch: plugin.json={plugin_version}, pyproject.toml={pyproject_version}"
        )


class TestSkillDirectories:
    def test_all_skill_dirs_have_skill_md(self):
        skills_dir = PROJECT_ROOT / "skills"
        if not skills_dir.exists():
            pytest.skip("No skills directory")

        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                assert (skill_dir / "SKILL.md").exists(), (
                    f"Skill directory '{skill_dir.name}' is missing SKILL.md"
                )


class TestHooksLayout:
    def test_hooks_json_valid(self):
        hooks_path = PROJECT_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            pytest.skip("No hooks.json")

        data = json.loads(hooks_path.read_text())
        assert "hooks" in data
        assert isinstance(data["hooks"], dict), "hooks must be a dict keyed by event name"

        valid_events = {"PreToolUse", "PostToolUse", "Stop", "SubagentStop",
                        "SessionStart", "SessionEnd", "UserPromptSubmit",
                        "PreCompact", "Notification"}
        for event, matchers in data["hooks"].items():
            assert event in valid_events, f"Unknown hook event: {event}"
            assert isinstance(matchers, list), f"hooks[{event}] must be a list of matcher objects"
            for matcher_obj in matchers:
                assert "matcher" in matcher_obj, f"Matcher in {event} missing 'matcher'"
                assert "hooks" in matcher_obj, f"Matcher in {event} missing 'hooks'"
                assert isinstance(matcher_obj["hooks"], list), f"Matcher hooks in {event} must be a list"
                for hook in matcher_obj["hooks"]:
                    assert "type" in hook, f"Hook in {event} missing 'type'"
                    assert hook["type"] in ("command", "prompt"), (
                        f"Hook type must be 'command' or 'prompt', got '{hook['type']}'"
                    )

    def test_hook_scripts_exist(self):
        hooks_path = PROJECT_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            pytest.skip("No hooks.json")

        data = json.loads(hooks_path.read_text())
        for event, matchers in data["hooks"].items():
            for matcher_obj in matchers:
                for hook in matcher_obj.get("hooks", []):
                    if hook.get("type") != "command":
                        continue
                    cmd = hook["command"]
                    cmd_resolved = cmd.replace("${CLAUDE_PLUGIN_ROOT}", str(PROJECT_ROOT))
                    parts = cmd_resolved.split()
                    script = parts[-1] if len(parts) > 1 else parts[0]
                    script_path = Path(script)
                    assert script_path.exists(), (
                        f"Hook in {event} references missing script: {script}"
                    )
