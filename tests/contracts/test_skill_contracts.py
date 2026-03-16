"""Contract tests for skill SKILL.md files.

Verifies that every skill conforms to structural requirements:
- Frontmatter with name and description (≥100 chars for matching)
- Tool references that use actual MCP tool names
- Numbered process steps
- Output contract reference or output format section
- Failure modes section
"""

import re
from pathlib import Path

import pytest

from tests.conftest import parse_frontmatter

SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"
SKILL_DIRS = sorted(SKILLS_DIR.iterdir()) if SKILLS_DIR.exists() else []

VALID_TOOL_PREFIX = "terminalq_"


def _skill_ids():
    return [d.name for d in SKILL_DIRS if (d / "SKILL.md").exists()]


def _load_skill(name: str) -> tuple[dict, str]:
    path = SKILLS_DIR / name / "SKILL.md"
    text = path.read_text()
    fm, body = parse_frontmatter(text)
    return fm, body


@pytest.fixture(params=_skill_ids())
def skill(request):
    name = request.param
    fm, body = _load_skill(name)
    return {"name": name, "frontmatter": fm, "body": body}


class TestSkillFrontmatter:
    def test_has_name(self, skill):
        assert "name" in skill["frontmatter"], f"{skill['name']}: missing 'name' in frontmatter"

    def test_has_description(self, skill):
        fm = skill["frontmatter"]
        assert "description" in fm, f"{skill['name']}: missing 'description' in frontmatter"

    def test_description_length(self, skill):
        desc = skill["frontmatter"].get("description", "")
        assert len(desc) >= 100, (
            f"{skill['name']}: description is {len(desc)} chars, need ≥100 for effective matching"
        )


class TestSkillBody:
    def test_has_tool_references(self, skill):
        refs = re.findall(r"terminalq_\w+", skill["body"])
        assert len(refs) > 0, f"{skill['name']}: no tool references (terminalq_*) found"

    def test_tool_references_use_valid_prefix(self, skill):
        refs = re.findall(r"`(\w+?)\(", skill["body"])
        tool_refs = [r for r in refs if r.startswith("terminalq_")]
        for ref in tool_refs:
            assert ref.startswith(VALID_TOOL_PREFIX), (
                f"{skill['name']}: tool ref '{ref}' doesn't start with '{VALID_TOOL_PREFIX}'"
            )

    def test_has_numbered_steps(self, skill):
        steps = re.findall(r"^\d+\.\s", skill["body"], re.MULTILINE)
        assert len(steps) >= 2, f"{skill['name']}: fewer than 2 numbered steps"

    def test_has_output_format_or_contract_ref(self, skill):
        body = skill["body"].lower()
        has_output = (
            "output" in body
            or "contract" in body
            or "briefing" in body
            or "report" in body
            or "scorecard" in body
            or "docs/output-contracts.md" in body
        )
        assert has_output, f"{skill['name']}: no output format section or contract reference"

    def test_has_failure_modes(self, skill):
        body = skill["body"].lower()
        assert "failure mode" in body or "## failure" in body, (
            f"{skill['name']}: missing Failure Modes section"
        )

    def test_has_when_not_to_use(self, skill):
        body = skill["body"].lower()
        assert "do not use" in body or "when not to use" in body, (
            f"{skill['name']}: missing 'Do not use' / 'When not to use' guidance"
        )

    def test_has_data_freshness_or_contract_ref(self, skill):
        body = skill["body"].lower()
        assert "data freshness" in body or "output-contracts.md" in body, (
            f"{skill['name']}: missing Data Freshness instruction or output contract reference"
        )

    def test_has_disclaimer_instruction(self, skill):
        body = skill["body"].lower()
        assert "disclaimer" in body or "not financial advice" in body or "output-contracts.md" in body, (
            f"{skill['name']}: missing disclaimer instruction or output contract reference"
        )
