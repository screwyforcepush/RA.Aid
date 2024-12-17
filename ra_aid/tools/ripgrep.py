from typing import Dict, Union, Optional, List
from langchain_core.tools import tool
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from ra_aid.proc.interactive import run_interactive_command
from ra_aid.text.processing import truncate_output

console = Console()

DEFAULT_EXCLUDE_DIRS = [
    '.git',
    'node_modules',
    'vendor',
    '.venv',
    '__pycache__',
    '.cache',
    'dist',
    'build',
    'env',
    '.env',
    'venv',
    '.idea',
    '.vscode'
]

@tool
def ripgrep_search(
    pattern: str,
    *,
    file_type: str = None,
    case_sensitive: bool = True,
    include_hidden: bool = False,
    follow_links: bool = False,
    exclude_dirs: List[str] = None
) -> Dict[str, Union[str, int, bool]]:
    """Execute a ripgrep (rg) search with formatting and common options.

    Args:
        pattern: Search pattern to find
        file_type: Optional file type to filter results (e.g. 'py' for Python files)
        case_sensitive: Whether to do case-sensitive search (default: True)
        include_hidden: Whether to search hidden files and directories (default: False)
        follow_links: Whether to follow symbolic links (default: False)
        exclude_dirs: Additional directories to exclude (combines with defaults)

    Returns:
        Dict containing:
            - output: The formatted search results
            - return_code: Process return code (0 means success)
            - success: Boolean indicating if search succeeded
    """
    # Build rg command with options
    cmd = ['rg']
    
    # Add options
    cmd.extend(['--color', 'always'])
    
    if not case_sensitive:
        cmd.append('-i')
    
    if include_hidden:
        cmd.append('--hidden')
        
    if follow_links:
        cmd.append('--follow')
        
    if file_type:
        cmd.extend(['-t', file_type])

    # Add exclusions - remove duplicates
    exclusions = list(set(DEFAULT_EXCLUDE_DIRS + (exclude_dirs or [])))
    
    # Add glob patterns - use ripgrep's native glob syntax without shell quoting
    for dir in exclusions:
        cmd.extend(['--glob', f'!{dir}'])

    # If pattern looks like a simple string (no regex chars), use fixed string mode
    if not any(c in pattern for c in r'[](){}.*+?^$|\\'):
        cmd.extend(['-F', pattern])  # Use fixed string mode
    else:
        cmd.extend(['--', pattern])  # Use regex mode with argument separator

    # Build info sections for display
    info_sections = []
    
    # Search parameters section
    params = [
        "## Search Parameters",
        f"**Pattern**: `{pattern}`",
        f"**Case Sensitive**: {case_sensitive}",
        f"**File Type**: {file_type or 'all'}"
    ]
    if include_hidden:
        params.append("**Including Hidden Files**: yes")
    if follow_links:
        params.append("**Following Symlinks**: yes")
    if exclude_dirs:
        params.append("\n**Additional Exclusions**:")
        for dir in exclude_dirs:
            params.append(f"- `{dir}`")
    info_sections.append("\n".join(params))

    # Display search info
    console.print(Panel(
        Markdown("\n".join(info_sections)),
        title="🔍 Ripgrep Search",
        border_style="blue"
    ))

    try:
        print()
        # Get count of searchable files first - without the search pattern
        cmd_files = cmd[:-1]  # Remove the search pattern
        cmd_files.extend(['--files'])
        files_output, _ = run_interactive_command(cmd_files)
        searchable_files = files_output.decode().strip().split('\n') if files_output else []
        total_files = len([f for f in searchable_files if f])  # Count non-empty lines

        # Now do the actual search with the pattern
        output, return_code = run_interactive_command(cmd)
        print()
        
        decoded_output = output.decode() if output else ""
        
        # Prepare result message
        if return_code == 0:
            # Found matches
            match_count = len([line for line in decoded_output.split('\n') if line.strip()])
            result_msg = [
                "✅ Found Matches!",
                f"Found {match_count} match{'es' if match_count != 1 else ''} in {total_files} searched files:",
                "",
                decoded_output
            ]
            decoded_output = "\n".join(result_msg)
        else:
            # No matches found
            result_msg = [
                "❌ No Matches Found",
                f"Searched {total_files} files for pattern: '{pattern}'",
                "",
                "File types included:" if file_type else "All file types searched",
            ]
            if file_type:
                result_msg.append(f"- {file_type}")
            if total_files > 0:
                result_msg.append("\nSample of files searched:")
                for file in searchable_files[:5]:  # Show first 5 files
                    if file:
                        result_msg.append(f"- {file}")
                if len(searchable_files) > 5:
                    result_msg.append(f"... and {len(searchable_files) - 5} more files")
            else:
                result_msg.append("\nNo matching files found to search!")
                
            decoded_output = "\n".join(result_msg)
        
        return {
            "output": truncate_output(decoded_output),
            "return_code": return_code,
            "success": return_code == 0
        }
        
    except Exception as e:
        error_msg = str(e)
        console.print(Panel(error_msg, title="❌ Error", border_style="red"))
        return {
            "output": error_msg,
            "return_code": 1
        }
