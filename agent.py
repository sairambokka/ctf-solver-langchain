import asyncio
from langchain_community.tools import ShellTool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent


async def main():
    llm = ChatOllama(
        model="minimax-m2:cloud",
        temperature=0.8,
    )

    client = MultiServerMCPClient(  
        {
            "kali-mcp": {
                "transport": "stdio",
                "command": "python3",
                "args": [
                    "/Users/sairambokka/Desktop/Code/MCP-Kali-Server/mcp_server.py",
                    "--server",
                    "http://172.16.237.128:5000/"
                ],
            },
        }
    )
    # No context manager here; directly await get_tools()
    mcp_tools = await client.get_tools()
    shell_tool = ShellTool()
    tools = mcp_tools + [shell_tool]

    # Initialize checkpointer and agent OUTSIDE the loop
    memory = InMemorySaver()
    
    SYSTEM_PROMPT = """You are an elite CTF Solver Agent specializing in Web Exploitation.
    Your goal is to solve Capture The Flag challenges given a URL or IP address.
    You have access to a shell to run commands. Use them to:
    1. Reconnaissance: Scan the target, check headers, view source (curl), look for robots.txt, cookies, etc.
    2. Enumeration: Identify valid pages, potential vulnerabilities, and inputs.
    3. Exploitation: Craft payloads to exploit vulnerabilities (SQLi, RCE, LFI, etc.).
    4. Flag Capture: Find and output the flag (format: flag{...}).

    CRITICAL: When using blocking network commands like 'nc' (netcat), ALWAYS use a timeout (e.g., 'nc -w 5 ...') or pipe input ('echo "input" | nc ...') to prevent the agent from hanging. Never run a raw blocking command.
    If using Python 'subprocess', NEVER use '.read()' without a timeout or loop. Use '.communicate(timeout=...)' instead.

    IMPORTANT: For running general commands like 'nc', 'curl', 'python3', etc., ALWAYS use the local 'terminal' tool. Only use specialized Kali MCP tools (like 'nikto_scan', 'sqlmap_scan') when specifically needed for those tasks.

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

    print("Model Ready. Type 'exit' to quit.")
    while True:
        # We can't use `input()` directly in async loop easily without blocking, 
        # but for this simple CLI it's acceptable or we can use a run_in_executor if needed.
        # For simplicity in this script we'll stick to blocking input since it's single user.
        user_input = input("User: ")
        if not user_input or user_input.lower() == "exit":
            break
            
        input_message = {
            "role": "user",
            "content": user_input,
        }

        async for step in agent.astream(
            {"messages": [input_message]},
            config,
            stream_mode="values",
        ):
            step["messages"][-1].pretty_print()

if __name__=="__main__":
    asyncio.run(main())
