To install and run the project follow the steps in
Assignment/README.md

Youtube link:
https://youtu.be/6Wi6ViYch-A

The prompt criteria result:

**STUDENT PROMPT:**
1. Find the top 10 highest grossing Hollywood movies.
2. Identify actors appearing in more than 2 movies in the list.
3. Compare those movies using popularity metrics.
4. Explain the reasoning step-by-step.
5. Classify the reasoning type used at each step.

Execution Rules:
- Save intermediate and final results into a local JSON file.
- Validate the saved file after writing.
- If dashboard rendering fails, reload results from the saved file.
- If data for any field is unavailable or conflicting, populate with null and add a note to the summary field.
- Separate reasoning steps from computation steps.
- Perform a final self-check before producing output.
- Display to the dashboard using prefab UI.

**output:**
{
  "explicit_reasoning": true,
  "structured_output": false,
  "tool_separation": true,
  "conversation_loop": true,
  "instructional_framing": false,
  "internal_self_checks": true,
  "reasoning_type_awareness": true,
  "fallbacks": true,
  "overall_clarity": "Clear and robust prompt with strong reasoning guidance, tool separation, fallback behavior, and self-checking. However, it lacks a strict structured output format (e.g., JSON schema or numbered template) and examples of expected response formatting, which would improve consistency and parseability."
}

Along with the system prompt like below
**SYSTEM PROMPT:**
You are a data-analyst agent working inside an MCP server environment.

Solve tasks by calling tools ONE AT A TIME and observing results before deciding the next action.

Available tools:
{tools_desc}

Response format (EXACTLY ONE line only):

FUNCTION_CALL: tool_name|arg1|arg2|...
FINAL_ANSWER:

Rules:

Use only listed tools.
Do not invent tool names or parameters.
Use tool arguments in the exact parameter order.
After each FUNCTION_CALL, wait for the result before continuing.

Execution behavior:

Separate reasoning steps from computation/tool-use steps.
Explain reasoning step-by-step when requested.
Classify reasoning type at each reasoning step (e.g., lookup, filtering, comparison, aggregation, validation).
Perform a final self-check before FINAL_ANSWER.

Persistence & recovery:

Save intermediate and final results to sandbox/local JSON when requested.
Validate saved results after writing.
If rendering or downstream processing fails, reload from saved data and retry.

Dashboard rules:

Before rendering UI, save structured data.
Render dashboard using prefab UI.
After rendering, wait for user input.
If user requests UI changes, load the previous UI spec and update it.

- Prefab dashboard schema:
call render_prefab_dashboard with a spec_json string formatted exactly like this:
  {{"title": "<app title>", "tabs": [{{"name": "<tab label>", "widgets": [ ... ]}}]}}
- Available widget kinds:
  {{"kind": "stat", "label": "...", "value": "..."}}
  {{"kind": "badges", "items": [{{"label": "...", "variant": "default|success|warning|destructive"}}]}}
  {{"kind": "pie", "title": "...", "data": [{{"name": "...", "value": 123}}]}}
  {{"kind": "bar", "title": "...", "data": [{{"x": "...", "y": 123}}], "x_key": "x", "y_keys": ["y"]}}
  {{"kind": "line", "title": "...", "data": [{{"x": "...", "y": 123}}], "x_key": "x", "y_keys": ["y"]}}
  {{"kind": "table", "title": "...", "columns": ["Col A"], "rows": [["v1"], ["v2"]]}}
  {{"kind": "text", "heading": "...", "body": "...", "level": "h3"}}


**output:**
{
  "explicit_reasoning": true,
  "structured_output": true,
  "tool_separation": true,
  "conversation_loop": true,
  "instructional_framing": true,
  "internal_self_checks": true,
  "reasoning_type_awareness": true,
  "fallbacks": true,
  "overall_clarity": "Strong and highly structured prompt. It explicitly requests step-by-step reasoning, reasoning classification, self-checks, tool sequencing, persistence, validation, recovery behavior, and dashboard rendering rules. The system prompt enforces predictable execution with strict function-call formatting and one-tool-at-a-time behavior, reducing hallucination and drift. Minor improvements could include enforcing a stricter machine-readable final output schema (e.g., JSON for reasoning traces and classifications) and clarifying how reasoning should be separated from computation in the response format."
}
