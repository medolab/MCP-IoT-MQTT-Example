import requests
import os
import json

API_KEY = os.environ.get("API_KEY", "supersecretapikey")
MCP_URL = os.environ.get("MCP_URL", "http://localhost:3000/mcp")
HEADERS = {"Content-Type": "application/json", "X-API-KEY": API_KEY}

def list_tools():
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    r = requests.post(MCP_URL, headers=HEADERS, json=payload)
    print("TOOLS:", r.status_code, r.text)

def call_tool(tool, args, rpc_id=2):
    payload = {"jsonrpc":"2.0","id":rpc_id,"method":"call_tool","params":{"tool":tool,"arguments":args}}
    r = requests.post(MCP_URL, headers=HEADERS, json=payload)
    print("CALL:", tool, r.status_code, r.text)

if __name__ == "__main__":
    list_tools()
    # Example: request to turn on fan202
    call_tool("turn_on", {"device_id":"fan202"})
    # Get status (may be "unknown" until device publishes)
    call_tool("get_status", {"device_id":"fan202"})
