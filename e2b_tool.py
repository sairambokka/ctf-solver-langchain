from typing import Optional, Type, Any
from langchain.tools import BaseTool
from e2b import Sandbox
import os
from pydantic import Field

class E2BShellTool(BaseTool):
    name: str = "terminal"
    description: str = (
        "Run shell commands inside a secure, isolated Kali Linux sandbox. "
        "Use this for all command execution, scanning, and exploitation. "
        "The sandbox has Kali tools like nmap, sqlmap, nikto, gobuster, and curl installed."
    )
    sandbox: Optional[Sandbox] = Field(default=None, exclude=True)

    def _get_sandbox(self) -> Sandbox:
        if self.sandbox is None:
            # We can specify a template ID here if we have one built.
            # For now, we'll use the default which we can customize.
            # If the user has built a template, they can put the ID in ENVs.
            template_id = os.getenv("E2B_TEMPLATE_ID")
            if template_id:
                self.sandbox = Sandbox.create(template=template_id)
            else:
                self.sandbox = Sandbox.create()
        return self.sandbox

    def _run(self, command: str) -> str:
        try:
            sb = self._get_sandbox()
            # Run the command in the sandbox
            output = sb.commands.run(command)
            
            if output.exit_code == 0:
                return output.stdout if output.stdout else "Command executed successfully (no output)."
            else:
                return f"Error (Exit {output.exit_code}):\n{output.stderr}\nOutput:\n{output.stdout}"
        except Exception as e:
            return f"Sandbox execution error: {str(e)}"

    async def _arun(self, command: str) -> str:
        # E2B SDK has an async client too, but for simplicity we'll wrap the sync one
        # or just implement it if the SDK supports it easily.
        # For now, let's stick to sync run which LangChain will run in an executor.
        return self._run(command)

    def close(self):
        if self.sandbox:
            self.sandbox.kill()
