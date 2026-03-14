# Task 2 Plan: The Documentation Agent

## Overview

Extend the agent from Task 1 with two tools (`read_file`, `list_files`) and an agentic loop that allows the LLM to iteratively query the project wiki before answering.

## Tool Definitions

### `read_file`

**Schema:**
```json
{
  "type": "function",
  "function": {
    "name": "read_file",
    "description": "Read the contents of a file from the project repository",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {"type": "string", "description": "Relative path from project root"}
      },
      "required": ["path"]
    }
  }
}
```

**Implementation:**
- Accept `path` parameter
- Validate: reject paths containing `..` or starting with `/`
- Resolve path relative to project root
- Return file contents as string, or error message if file doesn't exist

### `list_files`

**Schema:**
```json
{
  "type": "function",
  "function": {
    "name": "list_files",
    "description": "List files and directories at a given path",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {"type": "string", "description": "Relative directory path from project root"}
      },
      "required": ["path"]
    }
  }
}
```

**Implementation:**
- Accept `path` parameter
- Validate: reject paths containing `..` or starting with `/`
- List entries in the directory
- Return newline-separated listing

## Agentic Loop

### Data Structure

Track conversation as a list of messages:
```python
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_question},
    # ... tool calls and results appended here
]
```

### Loop Logic

```
1. Send messages + tool schemas to LLM
2. Parse response:
   - If tool_calls present:
     - Execute each tool
     - Append tool results as {"role": "tool", ...} messages
     - Increment tool call counter
     - If counter >= 10: stop and return current answer
     - Go to step 1
   - If no tool_calls (final answer):
     - Extract answer text
     - Extract source from answer (LLM should provide it)
     - Return JSON output
```

### System Prompt Strategy

The system prompt should instruct the LLM to:
1. Use `list_files` to discover wiki files
2. Use `read_file` to find relevant information
3. Include the source reference in the final answer (file path + section anchor)
4. Stop calling tools once enough information is gathered

## Path Security

**Threat:** User could try to read files outside project via `../../../etc/passwd`

**Mitigation:**
1. Reject any path containing `..`
2. Reject absolute paths (starting with `/`)
3. Use `Path.resolve()` and verify it's within project root
4. Return error message if path is invalid

## Output Format

Same as Task 1, but with populated fields:
```json
{
  "answer": "...",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {"tool": "list_files", "args": {"path": "wiki"}, "result": "..."},
    {"tool": "read_file", "args": {"path": "wiki/git-workflow.md"}, "result": "..."}
  ]
}
```

## Test Strategy

**Test 1:** Question about merge conflicts
- Input: `"How do you resolve a merge conflict?"`
- Expected: `read_file` in tool_calls, `wiki/git-workflow.md` in source

**Test 2:** Question about wiki contents
- Input: `"What files are in the wiki?"`
- Expected: `list_files` in tool_calls
