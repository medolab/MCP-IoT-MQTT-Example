import os
import threading
import time
import yaml
import logging
import paho.mqtt.client as mqtt

log = logging.getLogger("mqtt_client")
log.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
log.addHandler(handler)

# Load config
BASE_DIR = os.path.dirname(__file__)
cfg_path = os.path.join(BASE_DIR, "config.yaml")
with open(cfg_path, "r") as f:
    cfg = yaml.safe_load(f)

MQTT_HOST = os.environ.get("MQTT_BROKER", cfg.get("mqtt", {}).get("host", "localhost"))
MQTT_PORT = int(os.environ.get("MQTT_PORT", cfg.get("mqtt", {}).get("port", 1883)))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", cfg.get("mqtt", {}).get("username", ""))
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", cfg.get("mqtt", {}).get("password", ""))

# In-memory device status store
DEVICE_STATUS = {}

# Create client
client = mqtt.Client()

if MQTT_USERNAME:
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info("Connected to MQTT broker %s:%s", MQTT_HOST, MQTT_PORT)
        # Subscribe to device status topics (wildcard)
        client.subscribe("devices/+/status")
        log.info("Subscribed to devices/+/status")
    else:
        log.error("Failed to connect to broker, rc=%s", rc)


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode(errors="ignore")
    log.info("MQTT message %s => %s", topic, payload)
    # store last payload per topic
    DEVICE_STATUS[topic] = payload


client.on_connect = on_connect
client.on_message = on_message


def start_mqtt_loop():
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    # start a loop thread
    client.loop_start()
    # wait briefly for connection
    # (in production add robust reconnection/backoff)
    time.sleep(1)


def publish_command(device_id: str, command: str):
    topic = f"devices/{device_id}/cmd"
    log.info("Publishing %s => %s", topic, command)
    client.publish(topic, command)
    return True


def get_device_status(device_id: str):
    topic = f"devices/{device_id}/status"
    return DEVICE_STATUS.get(topic, "unknown")
