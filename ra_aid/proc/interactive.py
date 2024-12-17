"""
Module for running interactive subprocesses with output capture.
"""

import os
import re
import tempfile
import shlex
import shutil
from typing import List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

def run_interactive_command(cmd: List[str]) -> Tuple[bytes, int]:
    """
    Runs an interactive command with a pseudo-tty, capturing combined output.
    Works with both GNU and BSD variants of the script command.

Assumptions and constraints:
    - We are on a Unix-like system (Linux/macOS) with script command available
    - `cmd` is a non-empty list where cmd[0] is the executable
    - The executable and script are assumed to be on PATH
    - If anything is amiss (e.g., command not found), we fail early and cleanly
  
    Args:
        cmd: List of command parts where cmd[0] is the executable

    Returns:
        Tuple of (cleaned_output, return_code)
    """
    if not cmd:
        raise ValueError("No command provided.")
    
    if shutil.which(cmd[0]) is None:
        raise FileNotFoundError(f"Command '{cmd[0]}' not found in PATH.")

    # Display command info
    console.print(Panel(
        Markdown(f"Running command: `{' '.join(cmd)}`"),
        title="🔄 Interactive Command",
        border_style="bright_yellow"
    ))

    # Create temp files
    with tempfile.NamedTemporaryFile(prefix="script_", delete=False) as script_file:
        script_path = script_file.name
        # Write the command to a temporary shell script
        script_content = f"""#!/bin/bash
{' '.join(shlex.quote(c) for c in cmd)}
exit_code=$?
echo $exit_code > "{script_path}.retcode"
exit $exit_code
"""
        script_file.write(script_content.encode())
        os.chmod(script_path, 0o755)

    output_path = f"{script_path}.out"
    retcode_path = f"{script_path}.retcode"

    try:
        # Use BSD script syntax (macOS)
        os.system(f"script -q {shlex.quote(output_path)} {shlex.quote(script_path)}")
        
        # Read output
        with open(output_path, "rb") as f:
            output = f.read()
        
        # Clean ANSI escape sequences and control characters
        output = re.sub(rb'\x1b\[[0-9;]*[a-zA-Z]', b'', output)
        output = re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b'', output)
        
        # Get return code
        try:
            with open(retcode_path, "r") as f:
                return_code = int(f.read().strip())
        except (IOError, ValueError):
            return_code = 1

        # Display completion status
        status = "✅ Success" if return_code == 0 else "❌ Failed"
        console.print(Panel(
            f"Command completed with return code: {return_code}\n{status}",
            title="Command Result",
            border_style="green" if return_code == 0 else "red"
        ))

    except Exception as e:
        console.print(Panel(
            f"Error running interactive capture: {str(e)}",
            title="❌ Error",
            border_style="red"
        ))
        raise
    finally:
        # Cleanup
        for path in [script_path, output_path, retcode_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass

    return output, return_code
