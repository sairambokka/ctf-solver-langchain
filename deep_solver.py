import asyncio
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphRecursionError
from e2b_tool import E2BShellTool

# Load environment variables
load_dotenv()
from langchain_core.tools import Tool

# Import Deep Agents components
from deepagents import create_deep_agent

async def main():
    print("Initializing Deep CTF Solver...")
    
    # 1. Initialize LLMs
    main_llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=1.0,
    )
    sub_llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        temperature=1.0,
    )

    # 2. Initialize Tools (Sandbox)
    # Use E2B Sandbox for all sub-agents
    shell_tool = E2BShellTool()
    
    # 3. Tool Assignment
    # Since we are using a full Kali sandbox, all tools are available via 'terminal'
    recon_tools = [shell_tool]
    exploit_tools = [shell_tool]
    
    # 4. Define Sub-Agents
    RECON_PROMPT = """You are a Reconnaissance Specialist. 
    Your mission is to gather as much information as possible about the target using scanning tools.
    You have access to a secure Kali Linux sandbox via the 'terminal' tool.
    
    - Use 'terminal' to run:
        - 'nmap' for ports and services.
        - 'gobuster' or 'dirb' for directory enumeration.
        - 'nikto' for web vulnerabilities.
        - 'curl' for manual inspection.
    
    IMPORTANT: You have a limited number of steps (15). 
    If you are running out of steps, STOP scanning and report what you have found so far.
    
    CRITICAL: Do NOT attempt to exploit. Only report findings.
    Output your findings clearly."""

    EXPLOIT_PROMPT = """You are an Exploitation Specialist.
    Your mission is to use provided reconnaissance data to identify and exploit vulnerabilities.
    You have access to a secure Kali Linux sandbox via the 'terminal' tool.
    
    - Use 'terminal' to run:
        - 'sqlmap' for SQL injection.
        - 'hydra' for brute forcing.
        - 'msfconsole' or 'msfvenom' for exploits.
        - Manual payload crafting and delivery.
    
    IMPORTANT: You have a limited number of steps (15).
    If you are running out of steps, or if an exploit takes too long, STOP and report your progress.
    
    CRITICAL: Focus on getting the flag (flag{...})."""

    subagents = [
        {
            "name": "recon-specialist",
            "description": "A specialist agent for network scanning, port enumeration, directory busting, and web vulnerability scanning using Kali tools.",
            "system_prompt": RECON_PROMPT,
            "tools": recon_tools,
            "model": sub_llm,
        },
        {
            "name": "exploit-specialist",
            "description": "A specialist agent for aggressive exploitation, SQL injection, password cracking, and payload delivery using Kali tools.",
            "system_prompt": EXPLOIT_PROMPT,
            "tools": exploit_tools,
            "model": sub_llm,
        }
    ]


    # 5. Define Main System Prompt
    SYSTEM_PROMPT = """You are an Elite Deep CTF Solver Agent.
    Your mission is to solve Capture The Flag challenges methodically.

    You have access to:
    1. A virtual filesystem (via middleware) to store notes, plans, and evidence. USE IT.
    2. A 'task' tool to delegate complex work to sub-agents.
    
    WARNING: You do NOT have direct access to a terminal or scanning tools.
    You MUST delegate all execution, scanning, and exploitation to the appropriate sub-agent.

    Available Sub-Agents (use via 'task' tool):
    - 'recon-specialist': DELEGATE all information gathering, scanning (nmap, nikto), and manuall checks (curl, source code review) here.
    - 'exploit-specialist': DELEGATE specific exploitation attempts (sqlmap, payloads) here.

    Workflow:
    1. PLAN: Analyze the request.
    2. RECON: Use 'recon-specialist' to scan/check the target.
    3. ANALYZE: Review recon results. Formulate an attack vector.
    4. EXPLOIT: Use 'exploit-specialist' to execute the attack.
    5. REPORT: Output the flag when found.

    CRITICAL SAFETY:
    - Always use timeouts.
    - Prefer delegating heavy tools to sub-agents.
    """

    # 6. Create Deep Agent with Sub-Agents
    print("Building Agent Graph...")
    memory = InMemorySaver()
    
    # We pass 'shell_tool' as a default tool for the main agent too, plus maybe some lightweight ones if needed
    # The main agent primarily orchestrates via 'task' tool and file ops.
    main_tools = [] 
    
    agent_graph = create_deep_agent(
        model=main_llm,
        tools=main_tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=memory,
        subagents=subagents,
    )

    # 7. Run Interaction Loop
    MAX_STEPS = 20
    config = {
        "configurable": {"thread_id": "deep_session_1"},
        "recursion_limit": MAX_STEPS
    }
    
    import tui
    tui.print_welcome("Deep CTF Solver (Multi-Agent)")
    tui.print_info(f"Step Limit: {MAX_STEPS} per turn")
    
    try:
        while True:
            try:
                user_input = tui.get_user_input()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    break
                    
                input_message = {
                    "role": "user",
                    "content": user_input,
                }

                # Use 'stream' or 'astream' from the compiled graph
                try:
                    with tui.console.status("[bold green]Agents are working...[/bold green]"):
                        async for event in agent_graph.astream(
                            {"messages": [input_message]},
                            config,
                            stream_mode="values"
                        ):
                            # Using standard LangGraph print typical for 'values'
                            if "messages" in event:
                                msg = event["messages"][-1]
                                
                                # Handle Tool Messages (Results)
                                if hasattr(msg, "tool_call_id") or (hasattr(msg, "type") and msg.type == "tool"):
                                     if isinstance(msg.content, str):
                                        tui.print_tool_output(msg.content)
                                
                                # Handle AI Messages (Text + Tool Calls)
                                elif hasattr(msg, "content"):
                                    if isinstance(msg.content, str):
                                        tui.print_ai_message(msg.content)
                                    elif isinstance(msg.content, list):
                                        for block in msg.content:
                                            if isinstance(block, dict):
                                                if block.get("type") == "text":
                                                    tui.print_ai_message(block.get('text', ''))
                                                elif block.get("type") == "tool_use":
                                                    tool_name = block.get("name")
                                                    tool_input = block.get("input")
                                                    tui.print_tool_header(tool_name, str(tool_input))
                except GraphRecursionError:
                     tui.print_warning(f"Step limit ({MAX_STEPS}) reached. Execution stopped to save resources.")
                     tui.print_info("Hint: You can say 'continue' to resume if needed, or refine your prompt.")

            except Exception as e:
                tui.print_error(f"Error in loop: {e}")
    except KeyboardInterrupt:
        tui.print_info("\nInterrupted by user.")
    finally:
        tui.print_info("Cleaning up E2B Sandbox...")
        shell_tool.close()

if __name__=="__main__":
    asyncio.run(main())
