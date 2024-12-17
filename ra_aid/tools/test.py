from typing import Dict, Union, Optional, List
from langchain_core.tools import tool
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from ra_aid.proc.interactive import run_interactive_command
from ra_aid.text.processing import truncate_output

console = Console()

@tool
def run_test_command(
    command: str = "npm test",
    *,
    working_dir: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None
) -> Dict[str, Union[str, int, bool]]:
    """Execute a test command and return its results.
    
    This tool runs test commands like 'npm test', 'pytest', etc. and captures
    their output. It's designed to be used as part of the implementation
    feedback loop.

    Args:
        command: The test command to run (default: "npm test")
        working_dir: Optional working directory for the command
        env: Optional environment variables to set
        timeout: Optional timeout in seconds
        
    Returns:
        Dict containing:
            - output: The test output (stdout + stderr combined)
            - return_code: The process return code (0 typically means tests passed)
            - success: Boolean indicating if tests succeeded
    """
    # Display test info
    console.print(Panel(
        Markdown(f"Running tests: `{command}`"),
        title="🧪 Test Execution",
        border_style="bright_magenta"
    ))
    
    try:
        # Run the test command
        print()
        output, return_code = run_interactive_command(['/bin/bash', '-c', command])
        print()
        
        # Process results
        success = return_code == 0
        status = "✅ Tests Passed" if success else "❌ Tests Failed"
        
        # Show results panel
        console.print(Panel(
            Markdown(f"**Status**: {status}\n**Exit Code**: {return_code}"),
            title="Test Results",
            border_style="green" if success else "red"
        ))
        
        return {
            "output": truncate_output(output.decode()) if output else "",
            "return_code": return_code,
            "success": success
        }
        
    except Exception as e:
        error_msg = str(e)
        console.print(Panel(error_msg, title="❌ Error", border_style="red"))
        return {
            "output": error_msg,
            "return_code": 1,
            "success": False
        }