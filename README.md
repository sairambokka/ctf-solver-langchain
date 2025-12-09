# CTF Solver Agent

A specialized AI agent designed to solve Capture The Flag (CTF) challenges, typically in the Web Exploitation category.

## Overview

This project uses **LangChain** and **LangGraph** to create a conversational agent that:
1.  **Maintains Memory**: Uses `InMemorySaver` to remember context across turns.
2.  **Accesses Tools**:
    *   **Local Shell**: Executes commands like `curl`, `nc`, `python3` via `ShellTool`.
    *   **Kali Linux Tools**: Connects to a running **Model Context Protocol (MCP)** server on a Kali VM to access tools like `nikto`, `sqlmap`, `nmap`, etc.
3.  **Specialized Prompting**: Includes a system prompt tailored for Reconnaissance, Enumeration, and Exploitation workflows.

## Prerequisites

*   Python 3.10+
*   A running Kali Linux instance (VM or local) with the MCP Server installed.
*   Access to an LLM provider (currently configured for `minimax-m2:cloud` via Ollama/LangChain).

## Installation

1.  install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Run the agent:
    ```bash
    python3 agent.py
    ```

## Configuration

*   **Kali MCP**: Update the IP address in `agent.py` to match your Kali VM's IP address.
    ```python
    "args": [..., "--server", "http://YOUR_KALI_IP:5000/"]
    ```

## Usage

Start the agent and chat with it. Give it a target URL or IP.
*   "Scan http://target.com"
*   "Find the flag in this binary..."

## Notes
*   **Timeouts**: The agent is instructed to use timeouts (`-w 5`) for blocking commands like `nc`.
*   **Tools**: It prefers local shell tools for basic tasks (`curl`, `ls`) and Kali tools for heavy scanning.
