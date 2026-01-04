import asyncio
import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_ollama import ChatOllama
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent

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

    # NO TOOLS
    tools = []

    # Initialize checkpointer and agent OUTSIDE the loop
    memory = InMemorySaver()
    
    SYSTEM_PROMPT = """You are an elite CTF Solver Agent specializing in Web Exploitation.
    Your goal is to solve Capture The Flag challenges given a URL or IP address.
    You do NOT have access to any external tools. You must rely solely on your internal knowledge and reasoning.
    
    Workflow:
    1. Analyze the request.
    2. Suggest potential vulnerabilities or attack strings based on your training.
    3. Guide the user on what they should try manually.

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
    tui.print_welcome("CTF Solver Agent (No Tools)")

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
                    if hasattr(message, "content") and message.content:
                        if message.type == "ai":
                             tui.print_ai_message(message.content)

    except KeyboardInterrupt:
        tui.print_info("\nInterrupted by user.")
    except Exception as e:
        tui.print_error(f"Error: {e}")

if __name__=="__main__":
    asyncio.run(main())
