# mcp_photo_agent.py
# Usage:
#   python mcp_photo_agent.py --server "python" --args "photo_server.py" --folder "C:\\Users\\Chris\\OneDrive\\Pictures" --action organize

import argparse
import json
import subprocess
import threading
import queue
import uuid
import os

# --- Simple JSON-RPC client over stdio ---
class JsonRpcClient:
    def __init__(self, command, args=None, env=None):
        if args is None:
            args = []
        self.proc = subprocess.Popen(
            [command] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env or os.environ.copy()
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


# --- Agent wrapper for photo tools ---
class PhotoOrganizerAgent:
    def __init__(self, client: JsonRpcClient):
        self.client = client

    def list_photos(self, folder):
        return self.client.request("tools/call", {
            "name": "list_photos",
            "arguments": {"folder": folder}
        })

    def tag_photo(self, file, tags):
        return self.client.request("tools/call", {
            "name": "tag_photo",
            "arguments": {"file": file, "tags": tags}
        })

    def move_photo(self, file, destination):
        return self.client.request("tools/call", {
            "name": "move_photo",
            "arguments": {"file": file, "destination": destination}
        })

    def organize_by_date(self, folder):
        files = self.list_photos(folder)
        for f in files:
            meta = self.client.request("tools/call", {
                "name": "get_exif",
                "arguments": {"file": f}
            })
            date_str = meta.get("dateOriginal") or meta.get("date")
            if not date_str:
                continue
            from datetime import datetime
            d = datetime.fromisoformat(date_str)
            dest = os.path.join(folder, str(d.year), f"{d.month:02d}")
            self.move_photo(f, dest)


# --- CLI glue ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="python", help="Server command")
    parser.add_argument("--args", default="photo_server.py", help="Server args")
    parser.add_argument("--folder", default=os.path.expanduser("~/Pictures"))
    parser.add_argument("--action", choices=["list", "organize"], default="list")
    args = parser.parse_args()

    client = JsonRpcClient(args.server, args.args.split())
    agent = PhotoOrganizerAgent(client)

    try:
        if args.action == "list":
            files = agent.list_photos(args.folder)
            print("Found", len(files), "photos")
            for f in files:
                print(" -", f)
        elif args.action == "organize":
            agent.organize_by_date(args.folder)
            print("Organized photos by date.")
    finally:
        client.close()


if __name__ == "__main__":
    main()