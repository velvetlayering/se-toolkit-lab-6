"""Regression tests for agent.py."""

import json
import subprocess
import sys
from pathlib import Path


def run_agent(question: str) -> tuple[dict, str]:
    """Run agent.py with a question and return (parsed_json, stderr)."""
    result = subprocess.run(
        [sys.executable, "agent.py", question],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
        timeout=120,
    )
    stderr = result.stderr
    data = json.loads(result.stdout.strip())
    return data, stderr


def test_agent_returns_valid_json():
    """Test that agent.py returns valid JSON with required fields."""
    # Run agent.py with a simple question
    result = subprocess.run(
        [sys.executable, "agent.py", "What is 2 + 2?"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    # Check exit code
    assert result.returncode == 0, f"Agent failed: {result.stderr}"

    # Check stdout is valid JSON
    stdout = result.stdout.strip()
    assert stdout, "Agent produced no output"

    data = json.loads(stdout)

    # Check required fields exist
    assert "answer" in data, "Missing 'answer' field in output"
    assert "tool_calls" in data, "Missing 'tool_calls' field in output"

    # Check tool_calls is an array
    assert isinstance(data["tool_calls"], list), "'tool_calls' must be an array"

    # Check answer is non-empty
    assert data["answer"], "'answer' field is empty"


def test_merge_conflict_question_uses_read_file():
    """Test that a merge conflict question triggers read_file tool and returns wiki source."""
    data, stderr = run_agent("How do you resolve a merge conflict?")

    # Check required fields
    assert "answer" in data, "Missing 'answer' field"
    assert "source" in data, "Missing 'source' field"
    assert "tool_calls" in data, "Missing 'tool_calls' field"

    # Check that read_file was used
    tools_used = [tc.get("tool") for tc in data["tool_calls"]]
    assert "read_file" in tools_used, f"Expected read_file in tool_calls, got: {tools_used}"

    # Check that source points to wiki
    assert data["source"], "Source field is empty"
    assert "wiki/" in data["source"], f"Source should reference wiki, got: {data['source']}"

    # Check answer is non-empty
    assert len(data["answer"]) > 0, "Answer is empty"


def test_wiki_files_question_uses_list_files():
    """Test that a question about wiki contents triggers list_files tool."""
    data, stderr = run_agent("What files are in the wiki?")

    # Check required fields
    assert "answer" in data, "Missing 'answer' field"
    assert "tool_calls" in data, "Missing 'tool_calls' field"

    # Check that list_files was used
    tools_used = [tc.get("tool") for tc in data["tool_calls"]]
    assert "list_files" in tools_used, f"Expected list_files in tool_calls, got: {tools_used}"

    # Check answer is non-empty
    assert len(data["answer"]) > 0, "Answer is empty"
