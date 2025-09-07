# MCP IoT MQTT Example

This repo demonstrates a minimal MCP-style server that bridges JSON-RPC (MCP-like) calls to IoT devices over MQTT.

## Features

* `tools/list` discovery (returns available tools & JSON schemas)
* `call_tool` execution to run `turn_on`, `turn_off`, `get_status`
* MQTT integration (subscribe `devices/+/status`, publish `devices/<id>/cmd`)
* Simple API key auth via `X-API-KEY` header
* Docker-compose includes Mosquitto broker + MCP server
* ESP32 Arduino sketch to simulate a device

---

## Quick start (dev)

1. Copy `.env.example` to `.env` and edit if needed:

```bash
cp .env.example .env
# edit .env to set API_KEY if you want
```

2. Start stack with Docker Compose:

```bash
docker-compose up --build
```

This will:

* run Mosquitto MQTT broker on port `1883`
* run the MCP server on port `3000`

3. Test discovery (tools/list)

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: supersecretapikey" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

4. Test a tool call (turn\_on)

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: supersecretapikey" \
  -d '{"jsonrpc":"2.0","id":2,"method":"call_tool","params":{"tool":"turn_on","arguments":{"device_id":"fan202"}}}'
```

5. Inspect logs from the `mcp-server` container to see MQTT publishes, or use `mcp-server/scripts/test_client.py` for scripted tests.

---

## ESP32 device

Use `esp32/esp32_mqtt_example.ino` as a starting point. The device will:

* subscribe to `devices/<deviceId>/cmd`
* publish retain updates to `devices/<deviceId>/status`
* implement `on`, `off`, `toggle`

Configure `MQTT_BROKER` in the sketch to point at your broker IP.

---

## Production notes & security

* This example uses a simple API key. For production, use TLS, proper OAuth/DID auth, RBAC, and secure MQTT (TLS + client certs).
* Don't expose MQTT or the MCP endpoint to the open internet without strong authentication and encryption.
* Add logging, monitoring, and rate-limiting.
* Persist states in a DB if required.

---

## How to commit to GitHub

```bash
git init
git add .
git commit -m "Initial MCP IoT MQTT example"
# create remote and push as usual
```

---

## Next steps / extensions

* Add JWT/OAuth authentication.
* Add tool-level authorization (who can call `turn_on` vs `get_status`).
* Add blockchain verification hooks (for DePIN).
* Expand tool set (telemetry, firmware update, OTA).
