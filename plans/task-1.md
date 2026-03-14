# Task 1 Plan: Call an LLM from Code

## LLM Provider

- **Provider**: Qwen Code API
- **Model**: `qwen3-coder-plus`
- **Endpoint**: OpenAI-compatible chat completions API

## Architecture

The agent (`agent.py`) will have the following components:

### 1. Configuration Loading

Load API credentials from `.env.agent.secret`:
- `LLM_API_KEY` — API key for authentication
- `LLM_API_BASE` — Base URL of the LLM endpoint
- `LLM_MODEL` — Model name to use

### 2. LLM Client Function

A function that:
- Builds the HTTP request to the chat completions endpoint
- Sends the user's question as a user message
- Parses the LLM's response to extract the answer text

### 3. Output Formatting

Format the response as JSON:
```json
{"answer": "<LLM response text>", "tool_calls": []}
```

### 4. Main Entry Point

- Parse command-line argument (the question)
- Call the LLM client
- Print JSON to stdout
- Print any debug/progress info to stderr
- Exit with code 0 on success

## Error Handling

- If API call fails: print error to stderr, exit with non-zero code
- If response parsing fails: print error to stderr, exit with non-zero code
- Timeout: the subprocess runner enforces 60s timeout

## Dependencies

- `httpx` — already in `pyproject.toml`, for async HTTP requests
- Standard library: `json`, `os`, `sys`, `argparse`

## Test Strategy

One regression test that:
- Runs `agent.py "test question"` as a subprocess
- Parses stdout as JSON
- Asserts `answer` field exists
- Asserts `tool_calls` field exists and is an array
