# Agent Architecture

## Overview

This agent is a CLI tool that answers questions about the project by reading documentation from the wiki, examining source code, and querying the backend API. It uses an **agentic loop** to iteratively call tools, gather information, and produce a final answer with source references.

## LLM Provider

- **Provider**: Qwen Code API
- **Model**: `qwen3-coder-plus`
- **API Type**: OpenAI-compatible chat completions API

## How It Works

### Input

The agent takes a single command-line argument — the question:

```bash
uv run agent.py "How many items are in the database?"
```

### Agentic Loop

The agent runs an iterative loop:

1. **Send to LLM**: Current conversation (system prompt + user question + tool results) is sent to the LLM with tool definitions.
2. **Check for tool calls**: 
   - If the LLM returns `tool_calls`, execute each tool, append results to the conversation, and go back to step 1.
   - If the LLM returns a text message (no tool calls), that's the final answer.
3. **Output JSON**: Print the answer, source (if applicable), and tool call log to stdout.
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

The agent has three tools available:

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

#### `query_api`

Calls the backend API with optional authentication.

- **Parameters**: 
  - `method` (string) — HTTP method (GET, POST, PUT, DELETE, PATCH)
  - `path` (string) — API path (e.g., `/items/`, `/analytics/completion-rate`)
  - `body` (string, optional) — JSON request body for POST/PUT/PATCH
  - `auth` (boolean, default true) — Whether to include authentication header
- **Returns**: JSON string with `status_code` and `body`
- **Authentication**: Uses `LMS_API_KEY` from environment when `auth=true`

### System Prompt

The system prompt instructs the LLM to:

1. Choose the right tool based on the question type:
   - **Wiki questions** (how to do X, what files exist) → use `list_files` / `read_file` on wiki/
   - **System facts** (framework, ports, status codes) → use `query_api` or `read_file` on source code
   - **Data queries** (how many items, what score) → use `query_api`
   - **Bug diagnosis** → use `query_api` to reproduce error, then `read_file` to find the bug
2. Use `list_files` to discover relevant files if needed
3. Use `read_file` to read the content of relevant files
4. Use `query_api` to query the running backend for data or behavior
5. Provide a final answer with source reference if applicable

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
- **source** (string, optional): Reference to the wiki file or source code that contains the answer
- **tool_calls** (array): Log of all tool calls made during the agentic loop

### stdout vs stderr

- **stdout**: Only valid JSON output
- **stderr**: All debug/progress messages (e.g., "Calling LLM...", "Executing read_file...")

## File Structure

```
agent.py              # Main CLI with agentic loop and tools
.env.agent.secret     # LLM credentials (gitignored)
.env.docker.secret    # Backend API credentials (gitignored)
plans/
  task-1.md           # Task 1 implementation plan
  task-2.md           # Task 2 implementation plan
  task-3.md           # Task 3 implementation plan
AGENT.md              # This documentation
tests/
  test_agent.py       # Regression tests
```

## Configuration

### LLM Configuration (`.env.agent.secret`)

```bash
LLM_API_KEY=your-api-key-here
LLM_API_BASE=http://<vm-ip>:<port>/v1
LLM_MODEL=qwen3-coder-plus
```

### Backend Configuration (`.env.docker.secret`)

```bash
LMS_API_KEY=your-backend-api-key
```

### Environment Variables

The agent reads all configuration from environment variables for autochecker compatibility:

| Variable | Source | Default | Purpose |
|----------|--------|---------|---------|
| `LLM_API_KEY` | `.env.agent.secret` | — | LLM provider authentication |
| `LLM_API_BASE` | `.env.agent.secret` | — | LLM API endpoint |
| `LLM_MODEL` | `.env.agent.secret` | — | Model name |
| `LMS_API_KEY` | `.env.docker.secret` or env | — | Backend API authentication |
| `AGENT_API_BASE_URL` | Environment | `http://localhost:42002` | Backend API base URL |

**Important:** The autochecker injects its own values at runtime. No values are hardcoded.

## Running

```bash
# Basic usage
uv run agent.py "Your question here"

# Examples
uv run agent.py "What files are in the wiki?"
uv run agent.py "How do you resolve a merge conflict?"
uv run agent.py "What framework does the backend use?"
uv run agent.py "How many items are in the database?"
uv run agent.py "What status code does /items/ return without auth?"
```

## Testing

Run the regression tests:

```bash
uv run pytest tests/test_agent.py -v
```

Run the evaluation script to test against the autochecker questions:

```bash
uv run run_eval.py           # Run all 10 questions
uv run run_eval.py --index 0 # Run a single question
```

## Benchmark Results

The agent passes all 10 local evaluation questions:

| # | Question Type | Tools Used | Status |
|---|---------------|------------|--------|
| 0 | Wiki: branch protection | `read_file` | ✓ |
| 1 | Wiki: SSH connection | `read_file` | ✓ |
| 2 | Source: framework | `read_file` | ✓ |
| 3 | Source: router modules | `list_files` | ✓ |
| 4 | Data: item count | `query_api` | ✓ |
| 5 | System: status code | `query_api` | ✓ |
| 6 | Bug: division by zero | `query_api`, `read_file` | ✓ |
| 7 | Bug: NoneType error | `query_api`, `read_file` | ✓ |
| 8 | Reasoning: request journey | `read_file` | ✓ |
| 9 | Reasoning: idempotency | `read_file` | ✓ |

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

The `extract_source()` function uses regex to find source references in the LLM's answer. It looks for patterns like:
- `wiki/filename.md#section`
- `wiki/filename.md`
- `backend/app/file.py`

### Query API Authentication

The `query_api` tool has an optional `auth` parameter. This allows testing unauthenticated access (e.g., checking 401 responses) while defaulting to authenticated requests for data queries.

## Lessons Learned

1. **Tool descriptions matter**: Initially the LLM didn't use `query_api` for status code questions. Adding "Set auth=false to test unauthenticated access" to the description helped.

2. **Environment variable flexibility**: Reading from both `.env` files and direct environment variables ensures the agent works in local development and autochecker evaluation.

3. **Conversation format**: Using `assistant` role for tool results (instead of `tool` role) improved compatibility with the Qwen Code API.

4. **Source extraction**: The regex-based source extraction is imperfect but works for most cases. The LLM often includes file references in its answer naturally.

5. **Iterative debugging**: Running `run_eval.py` question-by-question (`--index N`) was essential for identifying and fixing specific failures.
