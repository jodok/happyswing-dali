#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <NTPClient.h>
#include <SimpleKalmanFilter.h>

// --- Config start ---

const char* topic = "sw1";

const char* ssid = "happyswing";
const char* password = "****";

const char* mqtt_server = "192.168.1.254";
const int mqtt_port = 1883;
const char* mqtt_username = "";
const char* mqtt_password = "";

const char* ntp_server = "pool.ntp.org";

const unsigned long send_interval_ms = 100;

const unsigned int measurement_buffer_size = 32;

// --- Config end ---

WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, ntp_server);

WiFiClient espClient;
PubSubClient client(espClient);

SimpleKalmanFilter kalmanAngle(10, 10, 1);

Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);

unsigned long bootUnixTime;
unsigned long bootMillisTime;

unsigned long lastUpdate = 0;

float measurements[measurement_buffer_size] = { 0.0 };

void setup() {
  Serial.begin(115200);
  setupWiFi();
  setupMQTT();
  setupUnix();
  setupAccel();
}

void loop() {
  sensors_event_t event;
  accel.getEvent(&event);

  float roll = atan2(-event.acceleration.y, -event.acceleration.z) * 180.0 / PI;
  float pitch = atan2(-event.acceleration.x, sqrt(event.acceleration.y * event.acceleration.y + event.acceleration.z * event.acceleration.z)) * 180.0 / PI;

  float angle = kalmanAngle.updateEstimate(roll);

  reconnectWiFiIfLost();

  if (client.connected() && ((millis() - lastUpdate) > send_interval_ms)) {
    char payload[250];

    float rms = calculateRMS();
    addNewMeasurement(angle);

    char* unix = readUnixTime();
    char* payload_mask = "{\"ts\": %s, \"angle\": %.2f, \"rms\": %.2f}";
    snprintf(payload, sizeof(payload), payload_mask, unix, angle, rms);
    client.publish(topic, payload);
    lastUpdate = millis();
  }

  client.loop();
  delay(10);
}

void addNewMeasurement(float value) {
  memcpy(measurements, &measurements[1], sizeof(measurements) - sizeof(float));
  measurements[measurement_buffer_size - 1] = value;
}

float calculateRMS() {
  float rms = 0;
  for (int i = 0; i < measurement_buffer_size; i++) {
    rms += measurements[i] * measurements[i];
  }
  return sqrt(rms / float(measurement_buffer_size));
}

char* readUnixTime() {
  unsigned long unix1 = bootUnixTime / 100000;
  unsigned long unix2 = (bootUnixTime % 100000) * 1000 + millis() - bootMillisTime;

  static char str[16];
  snprintf(str, sizeof(str), "%04lu%07lu", unix1, unix2);
  return str;
}

void callback(char* topic, byte* payload, unsigned int length) {}

void reconnectWiFiIfLost() {
  if ((WiFi.status() != WL_CONNECTED)) {
    Serial.println("Reconnecting to WiFi...");
    WiFi.disconnect();
    WiFi.reconnect();
  }
}

void setupWiFi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
}

void setupMQTT() {
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  while (!client.connected()) {
    Serial.println("Connecting to MQTT...");
    if (client.connect("ArduinoClient", mqtt_username, mqtt_password)) {
      Serial.println("Connected to MQTT");
    } else {
      Serial.print("MQTT Connection failed, rc=");
      Serial.print(client.state());
      Serial.println(" Retrying...");
      delay(5000);
    }
  }
}

void setupUnix() {
  timeClient.begin();
  timeClient.setTimeOffset(3600);

  while (!timeClient.update()) {}

  bootUnixTime = timeClient.getEpochTime();
  bootMillisTime = millis();
}

void setupAccel() {
  if (!accel.begin()) {
    Serial.println("Could not find a valid ADXL345 sensor, check wiring!");
    while (1);
  }
}
