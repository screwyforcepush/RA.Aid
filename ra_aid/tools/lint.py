from typing import Dict, Union, Optional, List
from pathlib import Path
import json
from langchain_core.tools import tool
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from ra_aid.proc.interactive import run_interactive_command
from ra_aid.text.processing import truncate_output

console = Console()

COMMON_LINTERS = {
    '.py': 'flake8',
    '.js': 'eslint',
    '.ts': 'eslint',
    '.jsx': 'eslint',
    '.tsx': 'eslint',
    '.rb': 'rubocop',
    '.go': 'golint',
    '.rs': 'clippy'
}

def get_npm_lint_command(working_dir: Optional[str] = None) -> Optional[str]:
    """Get the lint command from package.json if available."""
    try:
        pkg_path = Path(working_dir or '.') / 'package.json'
        if not pkg_path.exists():
            return None
            
        with open(pkg_path) as f:
            package_data = json.load(f)
            
        if isinstance(package_data, dict) and 'scripts' in package_data:
            if 'lint' in package_data['scripts']:
                return 'npm run lint'
                
        return None
        
    except Exception as e:
        console.print(f"[yellow]Warning: Error reading package.json: {e}[/yellow]")
        return None

@tool
def run_lint_command(
    *,
    files: Optional[List[str]] = None,
    auto_fix: bool = False,
    working_dir: Optional[str] = None,
) -> Dict[str, Union[str, int, bool]]:
    """Execute a linting command to check code quality.
    
    This tool runs linting tools and captures their output. It will:
    1. Use npm run lint if package.json is present (default)
    2. Fall back to detecting appropriate linter based on file extensions
    
    Args:
        files: Optional list of specific files to lint
        auto_fix: Whether to attempt automatic fixes
        working_dir: Optional working directory for the command
        
    Returns:
        Dict containing:
            - output: The lint output (stdout + stderr combined)
            - return_code: The process return code (0 typically means no issues)
            - success: Boolean indicating if linting passed
    """
    # First try to get npm lint command
    command = get_npm_lint_command(working_dir)
    
    # If no npm command and files specified, try to determine from files
    if not command and files:
        extensions = set(Path(f).suffix for f in files)
        linters = set(COMMON_LINTERS.get(ext) for ext in extensions)
        linters.discard(None)
        
        if len(linters) == 1:
            linter = linters.pop()
            if auto_fix:
                if linter == 'eslint':
                    command = f"{linter} --fix {' '.join(files)}"
                elif linter == 'flake8':
                    command = f"autopep8 --in-place {' '.join(files)}"
            else:
                command = f"{linter} {' '.join(files)}"
    
    if not command:
        return {
            "output": "No package.json lint script found and couldn't determine appropriate linter",
            "return_code": 1,
            "success": False
        }

    # Display lint info
    info_sections = [
        "## Lint Command",
        f"**Command**: `{command}`",
        f"**Auto Fix**: {'yes' if auto_fix else 'no'}"
    ]
    if files:
        info_sections.extend([
            "\n**Files**:",
            *[f"- `{f}`" for f in files]
        ])

    console.print(Panel(
        Markdown("\n".join(info_sections)),
        title="🔍 Lint Execution",
        border_style="blue"
    ))
    
    try:
        print()
        output, return_code = run_interactive_command(['/bin/bash', '-c', command])
        print()
        
        decoded_output = output.decode() if output else ""
        success = return_code == 0
        
        if not success:
            console.print(Panel(
                decoded_output,
                title="⚠️ Lint Issues Found",
                border_style="yellow"
            ))
        else:
            console.print("✅ No lint issues found!")
        
        return {
            "output": truncate_output(decoded_output),
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