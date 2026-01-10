from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from dotenv import load_dotenv
import subprocess
import queue
import threading
import uuid
import json
import sys
import os


load_dotenv()  # Load environment variables from .env file

# --- Simple JSON-RPC client over stdio ---
class JsonRpcClient:
    def __init__(self, command, args=None):
        if args is None:
            args = []
        self.proc = subprocess.Popen(
            [command] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=os.environ.copy()
        )
        self.responses = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                self.responses.put(msg)
            except Exception:
                # ignore non-JSON logs
                pass

    def request(self, method, params=None):
        req_id = uuid.uuid4().hex
        req = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        while True:
            resp = self.responses.get()
            if resp.get("id") == req_id:
                if "error" in resp:
                    raise Exception(resp["error"]["message"])
                return resp.get("result")

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.terminate()
        except Exception:
            pass


# Start the MCP server
client = JsonRpcClient(sys.executable, ["note_mcp_server.py"])

@tool
def read_note(filepath: str) -> str:
    """Read the contents of a text file."""
    return client.request("tools/call", {"name": "read_note", "arguments": {"filepath": filepath}})
    
@tool
def write_note(filepath: str, content: str) -> str:
    """Write content to a text file.  This will overwrite the file if it exists."""
    return client.request("tools/call", {"name": "write_note", "arguments": {"filepath": filepath, "content": content}})
    

TOOLS = [read_note, write_note]
SYSTEM_MESSAGE = """
You are a helpful note-taking assistant.  You have a cute name and you love to tell everyone your name.
You can read and write text files to help users manage their notes.
Be concise and helpful.  Be proactive in reading and writing notes as needed.
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
    finally:
        client.close()