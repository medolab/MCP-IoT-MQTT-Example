import os
import yaml
import logging
from flask import Flask, request, jsonify, abort
from mqtt_client import start_mqtt_loop, publish_command, get_device_status

# Logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mcp_server")

# Load config for API key default
BASE_DIR = os.path.dirname(__file__)
with open(os.path.join(BASE_DIR, "config.yaml"), "r") as f:
    cfg = yaml.safe_load(f)

API_KEY = os.environ.get("API_KEY", cfg.get("api_key", "changeme"))

# Define tool list (self-describing)
TOOLS = [
    {
        "name": "turn_on",
        "description": "Turn on a device",
        "input_schema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "device identifier (e.g. fan202)"}
            },
            "required": ["device_id"]
        }
    },
    {
        "name": "turn_off",
        "description": "Turn off a device",
        "input_schema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "device identifier"}
            },
            "required": ["device_id"]
        }
    },
    {
        "name": "get_status",
        "description": "Get the last known status of a device",
        "input_schema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string"}
            },
            "required": ["device_id"]
        }
    }
]

app = Flask(__name__)

def check_api_key(req):
    header = req.headers.get("X-API-KEY", "")
    if not header:
        # Also allow api_key in query param for convenience (not recommended prod)
        header = req.args.get("api_key", "")
    return header == API_KEY

@app.before_first_request
def start_background():
    # start the mqtt background loop once
    start_mqtt_loop()

@app.route("/mcp", methods=["POST"])
def mcp_endpoint():
    # Basic API key check - you can make discovery public but here we require API key
    if not check_api_key(request):
        # Return JSON-RPC style error
        payload = {"jsonrpc": "2.0", "id": None, "error": {"code": 401, "message": "Unauthorized - missing/invalid API key"}}
        return jsonify(payload), 401

    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}), 400

    method = data.get("method")
    rpc_id = data.get("id")

    # --- tools/list discovery ---
    if method == "tools/list":
        return jsonify({"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": TOOLS}})

    # --- call_tool: wrapper for tool execution ---
    if method == "call_tool":
        params = data.get("params", {})
        tool = params.get("tool")
        args = params.get("arguments", {}) or {}

        # Validate for required fields simplistically:
        if tool in ("turn_on", "turn_off", "get_status") and "device_id" not in args:
            return jsonify({"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32602, "message": "Missing required parameter 'device_id'"}}), 400

        if tool == "turn_on":
            device = args["device_id"]
            publish_command(device, "on")
            return jsonify({"jsonrpc": "2.0", "id": rpc_id, "result": {"device": device, "status": "requested"}})

        if tool == "turn_off":
            device = args["device_id"]
            publish_command(device, "off")
            return jsonify({"jsonrpc": "2.0", "id": rpc_id, "result": {"device": device, "status": "requested"}})

        if tool == "get_status":
            device = args["device_id"]
            status = get_device_status(device)
            return jsonify({"jsonrpc": "2.0", "id": rpc_id, "result": {"device": device, "status": status}})

        return jsonify({"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": "Tool not found"}}), 404

    # Unknown method
    return jsonify({"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": "Method not found"}}), 404


if __name__ == "__main__":
    # Optionally log the effective API key (don't do this in prod)
    log.info("Starting MCP server on :3000")
    log.info("API_KEY is set (not shown)")
    app.run(host="0.0.0.0", port=3000)
