import asyncio
import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_anthropic import ChatAnthropic
from langchain_community.tools import ShellTool
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load environment variables
load_dotenv()


async def main():
    # llm = ChatAnthropic(
    #     model="claude-haiku-4-5-20251001",
    #     temperature=0.8,
    # )
    # llm = ChatNVIDIA(
    # model="nvidia/nemotron-3-nano-30b-a3b", 
    # temperature=1,
    # top_p=1,
    # max_completion_tokens=16384,
    # extra_body={"chat_template_kwargs": {"enable_thinking":True}},
    # )

    llm = ChatOllama(
        model="devstral-2:123b-cloud",
        temperature=0.8,
    )

    # Initialize MCP Client (connecting to VM/Remote MCP)
    client = MultiServerMCPClient(  
        {
            "kali-mcp": {
                "transport": "stdio",
                "command": "python3",
                "args": [
                    "/Users/sairambokka/Desktop/Code/MCP-Kali-Server/mcp_server.py",
                    "--server",
                    "http://172.16.237.131:5000/"
                ],
            },
        }
    )
    # No context manager here; directly await get_tools()
    mcp_tools = await client.get_tools()

    # LOCAL SHELL TOOL
    shell_tool = ShellTool()
    
    # Combine MCP tools + Local Shell
    tools = mcp_tools + [shell_tool]

    # Initialize checkpointer and agent OUTSIDE the loop
    memory = InMemorySaver()
    
    SYSTEM_PROMPT = """You are an elite CTF Solver Agent specializing in Web Exploitation.
    Your goal is to solve Capture The Flag challenges given a URL or IP address.
    You have access to:
    1. A LOCAL shell (via 'terminal' tool) for basic commands like curl, ls, python3.
    2. Specialized Kali Linux tools (via MCP) like 'nmap_scan', 'sqlmap_scan', 'nikto_scan'.
    
    Use specialized tools when deep scanning is needed, and the local shell for quick checks or manual payloads.
    
    CRITICAL: When using blocking network commands like 'nc' (netcat), ALWAYS use a timeout (e.g., 'nc -w 5 ...') or pipe input to prevent hanging.
    
    Always plan your next step before executing. Be efficient and methodical.
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
    tui.print_welcome("CTF Solver Agent (Local + MCP)")

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
                        if message.type == "ai":
                             tui.print_ai_message(message.content)
                        elif message.type == "tool":
                             tui.print_tool_output(message.content)

    except KeyboardInterrupt:
        tui.print_info("\nInterrupted by user.")
    except Exception as e:
        tui.print_error(f"Error: {e}")

if __name__=="__main__":
    asyncio.run(main())
