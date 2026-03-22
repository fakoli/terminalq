"""Contract tests for command .md files.

Verifies that every command has:
- Frontmatter with name and description
- At least one tool reference
"""

import re
from pathlib import Path

import pytest

from tests.conftest import parse_frontmatter

COMMANDS_DIR = Path(__file__).resolve().parents[2] / "commands"
COMMAND_FILES = sorted(COMMANDS_DIR.glob("*.md")) if COMMANDS_DIR.exists() else []


def _command_ids():
    return [f.stem for f in COMMAND_FILES]


def _load_command(name: str) -> tuple[dict, str]:
    path = COMMANDS_DIR / f"{name}.md"
    text = path.read_text()
    fm, body = parse_frontmatter(text)
    return fm, body


@pytest.fixture(params=_command_ids())
def command(request):
    name = request.param
    fm, body = _load_command(name)
    return {"name": name, "frontmatter": fm, "body": body}


class TestCommandFrontmatter:
    def test_has_name(self, command):
        assert "name" in command["frontmatter"], f"/{command['name']}: missing 'name' in frontmatter"

    def test_has_description(self, command):
        assert "description" in command["frontmatter"], f"/{command['name']}: missing 'description' in frontmatter"


# Commands that are configuration/onboarding and don't invoke MCP tools
NO_TOOL_COMMANDS = {"tq-setup"}


class TestCommandBody:
    def test_has_tool_reference(self, command):
        if command["name"] in NO_TOOL_COMMANDS:
            pytest.skip(f"/{command['name']} is a config command — no MCP tools expected")
        refs = re.findall(r"terminalq_\w+", command["body"])
        assert len(refs) > 0, f"/{command['name']}: no tool references (terminalq_*) found"
