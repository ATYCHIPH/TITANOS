import os
import subprocess
import sys
import platform
import time
import shutil
from typing import List, Optional, Union, Dict

class Shell:
    """
    A cross-platform shell abstraction for executing commands.
    """
    
    @classmethod
    def get_default_shell(cls) -> Optional[str]:
        """Returns the default shell for the current platform."""
        system = platform.system()
        if system == "Windows":
            # Prefer PowerShell Core, then PowerShell, then CMD
            if cls.has_command("pwsh"):
                return "pwsh"
            if cls.has_command("powershell"):
                return "powershell"
            return "cmd"
        else:
            # Prefer bash, then zsh, then sh
            if cls.has_command("bash"):
                return "bash"
            if cls.has_command("zsh"):
                return "zsh"
            return "sh"

    @staticmethod
    def has_command(command: str) -> bool:
        """Checks if a command exists in the system PATH."""
        return shutil.which(command) is not None

    @classmethod
    def execute(
        cls,
        command: Union[str, List[str]],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        shell: bool = True,
        capture_output: bool = True,
        text: bool = True,
        timeout: Optional[int] = None,
        retries: int = 0,
        backoff: float = 1.0
    ) -> subprocess.CompletedProcess:
        """
        Executes a command cross-platform.
        
        Args:
            command: The command to execute (string or list of strings).
            cwd: The working directory.
            env: Environment variables.
            shell: Whether to use the shell.
            capture_output: Whether to capture stdout/stderr.
            text: Whether to return output as text.
            timeout: Command timeout in seconds.
        """
        system = platform.system()
        detected_shell = cls.get_default_shell()
        
        # On Windows, subprocess.run(shell=True) defaults to cmd.exe.
        # If we want to use powershell/pwsh, we need to wrap the command.
        if system == "Windows" and shell and detected_shell in ["pwsh", "powershell"]:
            if isinstance(command, str):
                # Use powershell -Command for strings
                command = [detected_shell, "-NonInteractive", "-NoProfile", "-Command", command]
            else:
                # Join list commands into a single command string for powershell
                cmd_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in command)
                command = [detected_shell, "-NonInteractive", "-NoProfile", "-Command", cmd_str]
            shell = False # We are now running the shell executable directly
            executable = None
        else:
            executable = detected_shell if shell else None
            # Standard subprocess behavior for other platforms or cmd
            if system == "Windows" and shell and executable == "cmd":
                executable = None

        attempt = 0
        max_attempts = retries + 1
        
        while True:
            attempt += 1
            result = subprocess.run(
                command,
                cwd=cwd,
                env={**os.environ, **(env or {})},
                shell=shell,
                executable=executable,
                capture_output=capture_output,
                text=text,
                timeout=timeout
            )
            
            if result.returncode == 0 or attempt >= max_attempts:
                return result
            
            time.sleep(backoff * (2 ** (attempt - 1)))

    @classmethod
    def run_hook(
        cls,
        hook_name: str,
        hooks_dir: str = "scripts",
        cwd: Optional[str] = None
    ) -> Optional[subprocess.CompletedProcess]:
        """
        Runs a shell hook script if it exists for the current platform.
        Looks for `{hook_name}.ps1` on Windows and `{hook_name}.sh` on Unix.
        """
        system = platform.system()
        ext = ".ps1" if system == "Windows" else ".sh"
        script_path = os.path.join(hooks_dir, f"{hook_name}{ext}")
        
        # If we didn't specify an absolute path or a cwd, we might need to resolve it
        if cwd:
            full_path = os.path.join(cwd, script_path)
        else:
            full_path = script_path
            
        if not os.path.exists(full_path):
            return None
            
        # Execute the script
        if system == "Windows":
            # Pass through powershell execution
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]
            return cls.execute(cmd, cwd=cwd, shell=False)
        else:
            # Execute bash script
            cmd = ["bash", script_path]
            return cls.execute(cmd, cwd=cwd, shell=False)

if __name__ == "__main__":
    # Quick test
    res = Shell.execute("echo Hello from TITANOS")
    print(f"Output: {res.stdout.strip()}")
    print(f"Platform: {platform.system()}")
    print(f"Shell: {Shell.get_default_shell()}")
