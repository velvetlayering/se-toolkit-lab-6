"""Regression tests for agent.py."""

import json
import subprocess
import sys
from pathlib import Path


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
