import os
import requests
from typing import List, Dict, Any
from langchain_core.tools import tool
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

@tool
def search_online(query: str) -> List[Dict[str, Any]]:
    """Search online for technical information, documentation, or code examples.
    
    This tool peforms a web search.
    Helpful for finding specific technical information and documentation.
    
    Args:
        query: The search query - be as specific as possible. Include the name of the library, language, or technology you are researching.
        
    Returns:
        List of search results from Jina AI
    """
    console.print(Panel(
        f"[blue]Searching online for:[/blue] {query}",
        title="🔍 Search Query",
        border_style="blue"
    ))
    
    jina_api_key = os.getenv('JINA_API_KEY')
    if not jina_api_key:
        console.print(Panel(
            "[yellow]JINA_API_KEY not set - online search disabled[/yellow]\n" +
            "Set the JINA_API_KEY environment variable to enable online search.",
            title="⚠️ Search Disabled",
            border_style="yellow"
        ))
        return []
    
    headers = {
        'Authorization': f'Bearer {jina_api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    data = {
        'q': query,
        'count': 3
    }
    
    try:
        response = requests.post('https://api.jina.ai/search', headers=headers, json=data)
        result = response.json()
        
        if result.get('code') == 200 and result.get('data'):
            processed_results = []
            for item in result['data']:
                # Remove links field for security
                if 'links' in item:
                    del item['links']
                processed_results.append(item)
            
            console.print(Panel(
                f"[green]Found {len(processed_results)} results[/green]",
                title="✅ Search Results",
                border_style="green"
            ))
            
            return processed_results
            
        return []
        
    except Exception as e:
        console.print(Panel(
            f"[red]Error performing online search: {str(e)}[/red]",
            title="❌ Search Error",
            border_style="red"
        ))
        return []