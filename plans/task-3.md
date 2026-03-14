# Task 3 Plan: The System Agent

## Overview

Extend the agent from Task 2 with a `query_api` tool that can call the deployed backend API. This enables the agent to answer both static system questions and data-dependent queries.

## New Tool: `query_api`

### Schema

```json
{
  "type": "function",
  "function": {
    "name": "query_api",
    "description": "Call the backend API with authentication",
    "parameters": {
      "type": "object",
      "properties": {
        "method": {"type": "string", "description": "HTTP method (GET, POST, etc.)"},
        "path": {"type": "string", "description": "API path (e.g., '/items/')"},
        "body": {"type": "string", "description": "Optional JSON request body"}
      },
      "required": ["method", "path"]
    }
  }
}
```

### Implementation

- Read `LMS_API_KEY` from `.env.docker.secret` for authentication
- Read `AGENT_API_BASE_URL` from environment (default: `http://localhost:42002`)
- Use `httpx` to make HTTP requests
- Return JSON string with `status_code` and `body`

## Environment Variables

The agent must read all configuration from environment variables:

| Variable | Source | Purpose |
|----------|--------|---------|
| `LLM_API_KEY` | `.env.agent.secret` | LLM provider authentication |
| `LLM_API_BASE` | `.env.agent.secret` | LLM API endpoint |
| `LLM_MODEL` | `.env.agent.secret` | Model name |
| `LMS_API_KEY` | `.env.docker.secret` | Backend API authentication |
| `AGENT_API_BASE_URL` | env or default | Backend API base URL |

**Important:** The autochecker injects its own values, so no hardcoded credentials.

## System Prompt Updates

Update the system prompt to guide the LLM on tool selection:

- **Wiki questions** (how to do X, what files exist) → use `list_files` / `read_file`
- **System facts** (framework, ports, status codes) → use `query_api` or `read_file` on source code
- **Data queries** (how many items, what score) → use `query_api`
- **Bug diagnosis** → use `query_api` to reproduce error, then `read_file` to find the bug

## Agentic Loop

The loop remains the same as Task 2:
1. Send question + all tool schemas to LLM
2. Execute tool calls, append results
3. Repeat until final answer or max 10 calls
4. Output JSON with `answer`, `source` (optional), `tool_calls`

## Benchmark Strategy

Run `uv run run_eval.py` and iterate:

1. First run: identify which questions fail
2. For each failure:
   - Check if the right tool was used
   - Check if the system prompt needs clarification
   - Check if the tool implementation has bugs
3. Re-run until all 10 questions pass

## Benchmark Results

**Initial Score:** 5/10 passed

**First Failures:**
1. Question 5 (status code without auth): Agent returned 200 instead of 401
   - **Cause**: `query_api` always sent auth header
   - **Fix**: Added optional `auth` parameter to `query_api` tool

2. Questions 6-9: Not yet tested
   - **Fix**: After fixing auth issue, all remaining questions passed

**Final Score:** 10/10 passed

**Iteration Strategy:**
- Used `run_eval.py --index N` to test individual questions
- Fixed `query_api` to support `auth=false` for testing unauthenticated access
- Updated tool description to guide LLM on when to use `auth=false`

## Test Strategy

**Test 1:** Backend framework question
- Input: `"What framework does the backend use?"`
- Expected: `read_file` in tool_calls, answer contains "FastAPI"

**Test 2:** Database query question
- Input: `"How many items are in the database?"`
- Expected: `query_api` in tool_calls, answer contains a number

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LLM doesn't use correct tool | Improve tool descriptions in schema |
| API authentication fails | Verify `LMS_API_KEY` is loaded correctly |
| Agent times out | Reduce max iterations, optimize prompts |
| Hardcoded values fail autochecker | Ensure all config comes from environment |
