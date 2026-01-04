import asyncio
import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from e2b_tool import E2BShellTool

# Load environment variables
load_dotenv()


async def main():
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0.8,
    )
    # llm = ChatNVIDIA(
    # model="nvidia/nemotron-3-nano-30b-a3b", 
    # temperature=1,
    # top_p=1,
    # max_completion_tokens=16384,
    # extra_body={"chat_template_kwargs": {"enable_thinking":True}},
    # )

    # llm = ChatOllama(
    #     model="devstral-2:123b-cloud",
    #     temperature=0.8,
    # )

    # Use E2B Sandbox instead of local shell or MCP tools
    shell_tool = E2BShellTool()
    tools = [shell_tool]

    # Initialize checkpointer and agent OUTSIDE the loop
    memory = InMemorySaver()
    
    SYSTEM_PROMPT = """You are an elite CTF Solver Agent specializing in Web Exploitation.
    Your goal is to solve Capture The Flag challenges given a URL or IP address.
    You have access to a secure Kali Linux sandbox via the 'terminal' tool. Use it to:
    1. Reconnaissance: Scan the target, check headers, view source (curl), look for robots.txt, cookies, etc.
    2. Enumeration: Identify valid pages, potential vulnerabilities, and inputs.
    3. Exploitation: Craft payloads to exploit vulnerabilities (SQLi, RCE, LFI, etc.).
    4. Flag Capture: Find and output the flag (format: flag{...}).

    CRITICAL: The 'terminal' tool runs in a remote sandbox. You can use it as a full Kali Linux environment. All hacking tools (nmap, sqlmap, nikto, etc.) are available through this tool.
    
    CRITICAL: When using blocking network commands like 'nc' (netcat), ALWAYS use a timeout (e.g., 'nc -w 5 ...') or pipe input ('echo "input" | nc ...') to prevent the agent from hanging. Never run a raw blocking command.
    
    IMPORTANT: Use the 'terminal' tool for all execution, scanning, and exploitation. Be efficient and methodical.
    """

    agent = create_agent(
        llm,
        tools,
        checkpointer=memory,
        system_prompt=SYSTEM_PROMPT, 
    )

    # Use a consistent thread_id for conversation history
    config = {"configurable": {"thread_id": "1"}}

    import tui
    tui.print_welcome("CTF Solver Agent (E2B)")

    try:
        while True:
            try:
                user_input = tui.get_user_input()
            except EOFError:
                break
                
            if not user_input or user_input.lower() == "exit":
                break
                
            input_message = {
                "role": "user",
                "content": user_input,
            }

            with tui.console.status("[bold green]Thinking...[/bold green]"):
                async for step in agent.astream(
                    {"messages": [input_message]},
                    config,
                    stream_mode="values",
                ):
                    message = step["messages"][-1]
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tool_call in message.tool_calls:
                            tui.print_tool_header(tool_call["name"], str(tool_call["args"]))
                    elif hasattr(message, "content") and message.content:
                         # Distinguish user vs AI
                        if message.type == "ai":
                             # Check if this AI message has tool calls.
                             # If it DOES have tool calls, the 'content' is usually the reasoning/scratchpad leading up to it.
                             if hasattr(message, "tool_calls") and message.tool_calls:
                                 if message.content:
                                     tui.print_thinking(message.content)
                             else:
                                 # If no tool calls, it's a final response or just chat
                                 # We can check for <think> tags if using deepseek/special models
                                 if "<think>" in message.content:
                                     # minimalist parsing for demo
                                     parts = message.content.split("</think>")
                                     thought = parts[0].replace("<think>", "").strip()
                                     rest = parts[1].strip() if len(parts) > 1 else ""
                                     tui.print_thinking(thought)
                                     if rest:
                                         tui.print_ai_message(rest)
                                 else:
                                     tui.print_ai_message(message.content)
                        elif message.type == "tool":
                             tui.print_tool_output(message.content)
    except KeyboardInterrupt:
        tui.print_info("\nInterrupted by user.")
    except Exception as e:
        tui.print_error(f"Error: {e}")
    finally:
        tui.print_info("Cleaning up E2B Sandbox...")
        shell_tool.close()

if __name__=="__main__":
    asyncio.run(main())
