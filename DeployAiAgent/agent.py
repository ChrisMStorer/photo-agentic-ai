from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

@tool
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
    
@tool
def write_note(filepath: str, content: str) -> str:
    """Write content to a text file.  This will overwrite the file if it exists."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to '{filepath}'."
    except Exception as e:
        return f"An error occurred while writing to {filepath}: {str(e)}"
    
TOOLS = [read_note, write_note]
SYSTEM_MESSAGE = """
You are a helpful note-taking assistant.  You have a cute name and you love to tell everyone your name.
You can read and write text files to help users manage their notes.
Be concise and helpful.
"""
llm = ChatOpenAI(temperature=0, model="gpt-4")
agent = create_agent(llm, TOOLS, system_prompt=SYSTEM_MESSAGE)

def run_agent(user_input: str) -> str:
    """Run the agent with a user query and return the response."""
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config={"recursion_limit": 50}
        )
        return result["messages"][-1].content
    except Exception as e:
        return f"Error {str(e)}"

print(run_agent("hello how are you?"))