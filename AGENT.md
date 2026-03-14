# Agent Architecture

## Overview

This agent is a CLI tool that answers questions about the project by reading documentation from the wiki. It uses an **agentic loop** to iteratively call tools, gather information, and produce a final answer with source references.

## LLM Provider

- **Provider**: Qwen Code API
- **Model**: `qwen3-coder-plus`
- **API Type**: OpenAI-compatible chat completions API

## How It Works

### Input

The agent takes a single command-line argument — the question:

```bash
uv run agent.py "How do you resolve a merge conflict?"
```

### Agentic Loop

The agent runs an iterative loop:

1. **Send to LLM**: Current conversation (system prompt + user question + tool results) is sent to the LLM with tool definitions.
2. **Check for tool calls**: 
   - If the LLM returns `tool_calls`, execute each tool, append results to the conversation, and go back to step 1.
   - If the LLM returns a text message (no tool calls), that's the final answer.
3. **Output JSON**: Print the answer, source, and tool call log to stdout.
4. **Max iterations**: The loop stops after 10 tool calls to prevent infinite loops.

```
Question ──▶ LLM ──▶ tool calls? ──yes──▶ execute tools ──▶ back to LLM
                     │
                     no
                     │
                     ▼
                JSON output
```

### Tools

The agent has two tools available:

#### `read_file`

Reads a file from the project repository.

- **Parameters**: `path` (string) — relative path from project root
- **Returns**: File contents as a string, or an error message
- **Security**: Rejects paths containing `..` or starting with `/` to prevent directory traversal

#### `list_files`

Lists files and directories at a given path.

- **Parameters**: `path` (string) — relative directory path from project root
- **Returns**: Newline-separated listing of entries, or an error message
- **Security**: Same path validation as `read_file`

### System Prompt

The system prompt instructs the LLM to:

1. Use `list_files` to discover relevant wiki files
2. Use `read_file` to read the content of relevant files
3. Provide a final answer with a source reference in the format `wiki/filename.md#section-anchor`
4. Stop calling tools once enough information is gathered

### Output Format

The agent outputs a single JSON line to stdout:

```json
{
  "answer": "...",
  "source": "wiki/git-vscode.md#resolve-a-merge-conflict",
  "tool_calls": [
    {
      "tool": "list_files",
      "args": {"path": "wiki"},
      "result": "..."
    },
    {
      "tool": "read_file",
      "args": {"path": "wiki/git.md"},
      "result": "..."
    }
  ]
}
```

- **answer** (string): The LLM's final answer to the question
- **source** (string): Reference to the wiki file and section that contains the answer
- **tool_calls** (array): Log of all tool calls made during the agentic loop

### stdout vs stderr

- **stdout**: Only valid JSON output
- **stderr**: All debug/progress messages (e.g., "Calling LLM...", "Executing read_file...")

## File Structure

```
agent.py              # Main CLI with agentic loop and tools
.env.agent.secret     # LLM credentials (gitignored)
plans/
  task-1.md           # Task 1 implementation plan
  task-2.md           # Task 2 implementation plan
AGENT.md              # This documentation
tests/
  test_agent.py       # Regression tests
```

## Configuration

Copy `.env.agent.example` to `.env.agent.secret` and fill in:

```bash
LLM_API_KEY=your-api-key-here
LLM_API_BASE=http://<vm-ip>:<port>/v1
LLM_MODEL=qwen3-coder-plus
```

## Running

```bash
# Basic usage
uv run agent.py "Your question here"

# Example
uv run agent.py "What files are in the wiki?"
uv run agent.py "How do you resolve a merge conflict?"
```

## Testing

Run the regression tests:

```bash
uv run pytest tests/test_agent.py -v
```

Run the evaluation script to test against the autochecker questions:

```bash
uv run run_eval.py           # Run all questions
uv run run_eval.py --index 0 # Run a single question
```

## Error Handling

- **Missing config file**: Exits with error message to stderr
- **API errors**: Prints status code and response to stderr
- **Path traversal attempts**: Returns error message, does not access files outside project
- **Timeout**: The runner enforces a 60-second timeout
- **Max tool calls**: Stops after 10 tool calls and synthesizes a final answer

## Security

The tools implement path validation to prevent directory traversal:

1. Reject any path containing `..`
2. Reject absolute paths (starting with `/`)
3. Use `Path.resolve()` and verify the resolved path is within project root

## Architecture Decisions

### Tool Response Format

Tool results are appended to the conversation as `assistant` messages with a `[Tool result: ...]` prefix. This format works with LLM providers that may not fully support the `tool` role.

### Source Extraction

The `extract_source()` function uses regex to find source references in the LLM's answer. It looks for patterns like `wiki/filename.md#section` or `wiki/filename.md`.
