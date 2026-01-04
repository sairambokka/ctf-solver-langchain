from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.theme import Theme
from rich.style import Style

# Custom Theme for CTF/Hacker vibes
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "error": "bold red",
    "danger": "bold red",
    "success": "bold green",
    "tool": "bold magenta",
    "user": "bold blue",
    "ai": "green",
    "timestamp": "dim white",
    "thinking": "dim italic cyan"
})

console = Console(theme=custom_theme)

def print_welcome(title: str = "CTF Solver Agent"):
    console.print(Panel.fit(
        f"[bold green]{title}[/bold green]\n[dim]Powered by LangChain & E2B[/dim]",
        border_style="green",
        padding=(1, 2)
    ))

def print_thinking(content: str):
    """Prints the internal thought process/scratchpad of the agent."""
    console.print(Panel(
        content,
        title="[thinking]💭 Reasoning[/thinking]",
        title_align="left",
        border_style="cyan",
        style="dim white",
        padding=(0, 2)
    ))

def print_user_message(content: str):
    console.print()
    console.print(Panel(
        content,
        title="[user]User[/user]",
        title_align="left",
        border_style="blue",
        padding=(1, 2)
    ))

def print_ai_message(content: str):
    console.print()
    md = Markdown(content)
    console.print(Panel(
        md,
        title="[ai]Agent[/ai]",
        title_align="left",
        border_style="green",
        padding=(1, 2)
    ))

def print_tool_header(tool_name: str, args: str):
    console.print(f"\n[tool]🔨 Executing {tool_name}...[/tool] [dim]({args})[/dim]")

def print_tool_output(output: str):
    # Truncate very long outputs for display to avoid flooding
    display_output = output
    if len(output) > 2000:
        display_output = output[:2000] + "\n... [truncated] ..."
        
    console.print(Panel(
        display_output,
        title="[tool]Tool Output[/tool]",
        title_align="left",
        border_style="magenta",
        style="dim white",
        padding=(0, 2)
    ))

def print_error(message: str):
    console.print(f"[error]❌ {message}[/error]")

def print_info(message: str):
    console.print(f"[info]ℹ️ {message}[/info]")

def print_success(message: str):
    console.print(f"[success]✅ {message}[/success]")

def get_user_input(prompt_text: str = "User") -> str:
    console.print()
    return Prompt.ask(f"[bold blue]{prompt_text}[/bold blue]")
