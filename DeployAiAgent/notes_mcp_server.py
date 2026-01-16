import asyncio
from fastmcp import FastMCP

server = FastMCP("notes-server")

@server.tool()
def read_note(filepath: str) -> str:
    """Read the contents of a text file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"Contents of {filepath}:\n{content}"
    except FileNotFoundError:
        return f"Error: The file {filepath} was not found."
    except Exception as e:
        return f"An error occurred while reading {filepath}: {str(e)}"

@server.tool()
def write_note(filepath: str, content: str) -> str:
    """Write content to a text file. This will overwrite the file if it exists."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to '{filepath}'."
    except Exception as e:
        return f"An error occurred while writing to {filepath}: {str(e)}"

if __name__ == "__main__":
    server.run(transport="stdio")