import asyncio
import os
import sys
import subprocess
import socket
from concurrent.futures import TimeoutError

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Ensure the local directory is in the path for importing client and schemas
sys.path.insert(0, os.path.dirname(__file__))
from client import LLM

# Load the .env from the local directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_V2_URL", "http://localhost:8100")
PROVIDER = os.getenv("GATEWAY_PROVIDER", "gemini")
MODEL = os.getenv("GATEWAY_MODEL", "gemini-3.1-flash-lite")

MAX_ITERATIONS = 8
LLM_SLEEP_SECONDS = 5
LLM_TIMEOUT = 120

# Initialize local LLM client for LLM Gateway V2
gateway_client = LLM(base_url=LLM_GATEWAY_URL, timeout=LLM_TIMEOUT)

def get_gateway_python():
    gateway_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "llm_gatewayV2"))
    if os.name == "nt":
        venv_python = os.path.join(gateway_dir, ".venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(gateway_dir, ".venv", "bin", "python")
        
    if os.path.exists(venv_python):
        return venv_python
    return sys.executable

async def ensure_gateway_running():
    gateway_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "llm_gatewayV2"))
    
    # Extract port from LLM_GATEWAY_URL (default to 8100)
    port = 8100
    try:
        from urllib.parse import urlparse
        parsed = urlparse(LLM_GATEWAY_URL)
        if parsed.port:
            port = parsed.port
    except Exception:
        pass

    # Check if port is open
    is_open = False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect(("127.0.0.1", port))
            is_open = True
        except Exception:
            pass
            
    if is_open:
        print(f"LLM Gateway V2 is already running on port {port}.")
        return
        
    print(f"LLM Gateway V2 is not running. Launching in background on port {port}...")
    python_exe = get_gateway_python()
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["GATEWAY_V2_PORT"] = str(port)
    
    log_path = os.path.join(os.path.dirname(__file__), "sandbox", "gateway_log.txt")
    log_file = open(log_path, "w", encoding="utf-8")
    
    if os.name == "nt":
        subprocess.Popen(
            [python_exe, "main.py"],
            cwd=gateway_dir,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            env=env,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
        )
    else:
        subprocess.Popen(
            [python_exe, "main.py"],
            cwd=gateway_dir,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            env=env,
            start_new_session=True
        )
        
    print("Waiting for LLM Gateway V2 to start...")
    for _ in range(20):
        await asyncio.sleep(0.5)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect(("127.0.0.1", port))
                print(f"LLM Gateway V2 is ready on port {port}.")
                return
            except Exception:
                pass
    print(f"Warning: LLM Gateway V2 failed to respond on port {port}. It might still be starting up.")

async def generate_with_timeout(prompt: str, provider: str, model: str, timeout: int = LLM_TIMEOUT):
    """Call the LLM Gateway V2 chat endpoint asynchronously and return standard ChatResponse."""
    loop = asyncio.get_event_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(
            None,
            lambda: gateway_client.chat(
                prompt=prompt,
                provider=provider,
                model=model,
                max_tokens=2048,
                temperature=0.7
            )
        ),
        timeout=timeout,
    )


def describe_tools(tools) -> str:
    lines = []
    for i, t in enumerate(tools, 1):
        props = (t.inputSchema or {}).get("properties", {})
        params = ", ".join(f"{n}: {p.get('type', '?')}" for n, p in props.items()) or "no params"
        lines.append(f"{i}. {t.name}({params}) — {t.description or ''}")
    return "\n".join(lines)


async def main():
    await ensure_gateway_running()
    mcp_script_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", mcp_script_path],
    )
    # Note: if uv is not present, we fallback to python
    # For now, we assume uv run or just python is in path. 
    # Let's just use "python" directly to be safer if `uv` isn't configured for standard scripts
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[mcp_script_path],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to Assignment MCP server")

            tools = (await session.list_tools()).tools
            tools_desc = describe_tools(tools)
            print(f"Loaded {len(tools)} tools\n")

            system_prompt = f"""You are a data-analyst agent working inside an MCP server environment.

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
"""

            print("\n" + "="*50)
            print("Agent is ready! Type your request and press Enter.")
            print("Press Ctrl+C to exit at any time.")
            print("="*50)
            
            prompt_log_path = os.path.join(os.path.dirname(__file__), "sandbox", "prompt_log.txt")
            
            history: list[str] = []
            
            while True:
                try:
                    user_input = input("\nWhat more can I do for you? (Ctrl+C to exit): ").strip()
                    if not user_input:
                        continue
                    task = user_input
                except (KeyboardInterrupt, EOFError):
                    print("\nExiting agent loop.")
                    sys.exit(0)

                history.append(f"\n--- New Task: {task} ---")

                # Dynamically retrieve available gateway providers to set up backup rotators
                try:
                    caps = gateway_client.capabilities()
                    llm_order_raw = os.getenv("LLM_ORDER", "gemini,groq,cerebras,openrouter,github,nvidia")
                    order = [p.strip() for p in llm_order_raw.split(",") if p.strip()]
                    
                    provider_candidates = []
                    for p in order:
                        if p in caps:
                            provider_candidates.append((p, caps[p]["model"]))
                    for p in caps:
                        if p not in order:
                            provider_candidates.append((p, caps[p]["model"]))
                except Exception as e:
                    print(f"Error fetching capabilities: {e}. Using static fallbacks.")
                    provider_candidates = [
                        ("gemini", "gemini-3.1-flash-lite"),
                        ("groq", "llama-3.3-70b-versatile"),
                        ("cerebras", "qwen-3-235b-a22b-instruct-2507"),
                        ("openrouter", "nvidia/nemotron-3-super-120b-a12b:free"),
                        ("github", "Llama-4-Scout-17B-16E-Instruct"),
                        ("nvidia", "deepseek-ai/deepseek-v4-pro")
                    ]

                # Select up to 3 unique providers beginning with the default PROVIDER/MODEL
                chosen_providers = [(PROVIDER, MODEL)]
                for p, m in provider_candidates:
                    if len(chosen_providers) >= 3:
                        break
                    if not any(cp[0] == p for cp in chosen_providers):
                        chosen_providers.append((p, m))

                while len(chosen_providers) < 3 and provider_candidates:
                    chosen_providers.append(provider_candidates[0])

                got_final_answer = False
                current_provider_idx = 0

                while current_provider_idx < len(chosen_providers) and not got_final_answer:
                    curr_prov, curr_model = chosen_providers[current_provider_idx]
                    print(f"\n=== Running with Provider: {curr_prov} | Model: {curr_model} (Attempt {current_provider_idx + 1}/3) ===")
                    history.append(f"\n--- Starting attempt with provider: {curr_prov} ({curr_model}) ---")

                    for iteration in range(1, MAX_ITERATIONS + 1):
                        print(f"\n--- [Provider: {curr_prov}] Iteration {iteration} ---")

                        context = "\n".join(history) if history else "(no prior steps)"
                        prompt = (
                            f"{system_prompt}\n"
                            f"Task: {task}\n\n"
                            f"Previous steps:\n{context}\n\n"
                            f"What is your next single action?"
                        )

                        print(f"Sleeping {LLM_SLEEP_SECONDS}s before LLM call...")
                        
                        with open(prompt_log_path, "a", encoding="utf-8") as f:
                            f.write(f"\n=== Task: {task} | Provider: {curr_prov} | Model: {curr_model} | Iteration: {iteration} ===\n")
                            f.write(f"PROMPT:\n{prompt}\n")
                            f.write("=" * 50 + "\n")

                        await asyncio.sleep(LLM_SLEEP_SECONDS)

                        try:
                            response = await generate_with_timeout(prompt, provider=curr_prov, model=curr_model)
                        except (TimeoutError, asyncio.TimeoutError):
                            print(f"LLM timed out on provider {curr_prov} — stopping iterations for this provider.")
                            history.append(f"Iteration {iteration} ({curr_prov}): TimeoutError")
                            break
                        except Exception as e:
                            print(f"LLM error on provider {curr_prov}: {e}")
                            history.append(f"Iteration {iteration} ({curr_prov}): Error: {e}")
                            break

                        text = (response.text or "").strip().splitlines()[0].strip()
                        print(f"LLM ({curr_prov}): {text}")

                        if text.startswith("FINAL_ANSWER:"):
                            print(f"\n=== Agent done (Provider: {curr_prov}) ===")
                            print(text)
                            history.append(f"Iteration {iteration} ({curr_prov}): gave {text}")
                            got_final_answer = True
                            break

                        if not text.startswith("FUNCTION_CALL:"):
                            print(f"Unexpected response format from provider {curr_prov} — stopping iterations for this provider.")
                            history.append(f"Iteration {iteration} ({curr_prov}): Unexpected response: {text}")
                            break

                        _, call = text.split(":", 1)
                        parts = [p.strip() for p in call.split("|")]
                        func_name, raw_args = parts[0], parts[1:]

                        tool = next((t for t in tools if t.name == func_name), None)
                        if tool is None:
                            msg = f"Unknown tool {func_name!r}"
                            print(msg)
                            history.append(f"Iteration {iteration} ({curr_prov}): {msg}")
                            continue

                        props = (tool.inputSchema or {}).get("properties", {})
                        
                        # Make sure we don't try to zip more args than properties
                        if len(raw_args) > len(props):
                            raw_args = raw_args[:len(props)]
                        elif len(raw_args) < len(props):
                            # padding with empty strings
                            raw_args += [""] * (len(props) - len(raw_args))

                        arguments = {
                            name: val
                            for name, val in zip(props.keys(), raw_args)
                        }

                        print(f"-> {func_name}({arguments})")
                        try:
                            result = await session.call_tool(func_name, arguments=arguments)
                            payload = (
                                result.content[0].text
                                if result.content and hasattr(result.content[0], "text")
                                else str(result)
                            )
                        except Exception as e:
                            payload = f"ERROR: {e}"

                        print(f"<- [Result length: {len(payload)} chars]")
                        
                        history_payload = payload
                        if len(payload) > 2000:
                            history_payload = (
                                payload[:1500] 
                                + f"\n... [Truncated {len(payload) - 2000} characters of output] ...\n" 
                                + payload[-500:]
                            )

                        history.append(
                            f"Iteration {iteration} ({curr_prov}): called {func_name}({arguments}) -> {history_payload}"
                        )
                        
                        #history.append(
                        #    f"Iteration {iteration} ({curr_prov}): called {func_name}({arguments}) -> {payload}"
                        #)
                        
                    else:
                        print(f"\nReached MAX_ITERATIONS({MAX_ITERATIONS}) on provider {curr_prov} without FINAL_ANSWER.")
                        history.append(f"\n--- Reached MAX_ITERATIONS({MAX_ITERATIONS}) on provider {curr_prov} without FINAL_ANSWER ---")

                    if not got_final_answer:
                        current_provider_idx += 1
                        if current_provider_idx < len(chosen_providers):
                            next_prov, next_model = chosen_providers[current_provider_idx]
                            print(f"\n[Switching Provider] 8 iterations reached. Switching from {curr_prov} to {next_prov}...")
                        else:
                            print(f"\n[Terminated] Reached max iterations (8) across all 3 providers without a FINAL_ANSWER.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
