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
import logging


load_dotenv()  # Load environment variables from .env file

logging.basicConfig(level=logging.INFO, filename='photo_agent.log', filemode='a')

# --- Simple JSON-RPC client over stdio ---
class JsonRpcClient:
    def __init__(self, command, args=None):
        if args is None:
            args = []
        logging.info(f"Starting MCP server process: {command} {' '.join(args)}")
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
                logging.info(f"Received message: {msg}")
            except Exception:
                # ignore non-JSON logs
                pass

    def request(self, method, params=None):
        req_id = uuid.uuid4().hex
        req = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}
        logging.info(f"Sending request: {req}")
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        while True:
            resp = self.responses.get()
            if resp.get("id") == req_id:
                if "error" in resp:
                    logging.error(f"Error in response: {resp['error']}")
                    raise Exception(resp["error"]["message"])
                logging.info(f"Received response: {resp}")
                return resp.get("result")

    def close(self):
        logging.info("Closing MCP server process")
        try:
            self.proc.stdin.close()
            self.proc.terminate()
        except Exception:
            pass


# Start the MCP server
client = JsonRpcClient(sys.executable, ["photo_mcp_server.py"])

@tool
def get_location_name_from_gps_coords(latitude: float, longitude: float) -> str:
    """Get location name from GPS coordinates using Nominatim API"""
    logging.info(f"Calling get_location_name_from_gps_coords with lat: {latitude}, lon: {longitude}")
    return client.request("tools/call", {"name": "get_location_name_from_gps_coords", "arguments": {"latitude": latitude, "longitude": longitude}})
    
@tool
def get_image_location_metadata(filepath: str) -> str:
    """Get image location metadata from a file using ExifRead"""
    logging.info(f"Calling get_image_location_metadata for file: {filepath}")
    return client.request("tools/call", {"name": "get_image_location_metadata", "arguments": {"filepath": filepath}})

TOOLS = [get_location_name_from_gps_coords, get_image_location_metadata]
SYSTEM_MESSAGE = """
You are a helpful photo agent.  You have a cute name and you love to tell everyone your name.
You can read images and find out where they were taken.
Be concise and helpful.
"""
llm = ChatOpenAI(temperature=0, model="gpt-4")
agent = create_agent(llm, TOOLS, system_prompt=SYSTEM_MESSAGE)

def run_agent(user_input: str) -> str:
    """Run the agent with a user query and return the response."""
    logging.info(f"Running agent with input: {user_input}")
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config={"recursion_limit": 50}
        )
        response = result["messages"][-1].content
        logging.info(f"Agent response: {response}")
        return response
    except Exception as e:
        logging.error(f"Error running agent: {str(e)}")
        return f"Error {str(e)}"
    finally:
        client.close()