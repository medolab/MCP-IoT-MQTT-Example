/*
  Minimal ESP32 MQTT example (PubSubClient)
  - Replace WIFI_SSID, WIFI_PASS, MQTT_BROKER
  - deviceId is used in topics devices/<deviceId>/cmd and devices/<deviceId>/status
*/

#include <WiFi.h>
#include <PubSubClient.h>

const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";
const char* MQTT_BROKER = "192.168.1.100"; // or hostname of your broker
const int MQTT_PORT = 1883;

const char* deviceId = "fan202";

WiFiClient espClient;
PubSubClient client(espClient);

const int OUTPUT_PIN = 2; // change to your pin controlling the relay

void publishStatus(const char* status) {
  char topic[64];
  snprintf(topic, sizeof(topic), "devices/%s/status", deviceId);
  client.publish(topic, status, true); // retain = true so server has last state
}

void callback(char* topic, byte* payload, unsigned int length) {
  payload[length] = 0;
  String msg = String((char*)payload);
  Serial.print("Received: ");
  Serial.print(topic);
  Serial.print(" -> ");
  Serial.println(msg);

  if (msg == "on") {
    digitalWrite(OUTPUT_PIN, HIGH);
    publishStatus("on");
  } else if (msg == "off") {
    digitalWrite(OUTPUT_PIN, LOW);
    publishStatus("off");
  } else if (msg == "toggle") {
    digitalWrite(OUTPUT_PIN, !digitalRead(OUTPUT_PIN));
    publishStatus(digitalRead(OUTPUT_PIN) ? "on" : "off");
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(deviceId)) {
      Serial.println("connected");
      char cmdTopic[64];
      snprintf(cmdTopic, sizeof(cmdTopic), "devices/%s/cmd", deviceId);
      client.subscribe(cmdTopic);
      // publish initial state
      publishStatus("off");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5s");
      delay(5000);
    }
  }
}

void setup() {
  pinMode(OUTPUT_PIN, OUTPUT);
  digitalWrite(OUTPUT_PIN, LOW);
  Serial.begin(115200);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("connected");
  client.setServer(MQTT_BROKER, MQTT_PORT);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  // Optionally publish telemetry periodically:
  static unsigned long last = 0;
  if (millis() - last > 30000) {
    last = millis();
    publishStatus(digitalRead(OUTPUT_PIN) ? "on" : "off");
  }
}
