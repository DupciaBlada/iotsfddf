#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// WiFi credentials
const char* ssid = "chatabogata";
const char* password = "dupciablada";

// MQTT Broker settings
const int mqtt_port = 8883;
const char* mqtt_broker = "h7349222.ala.eu-central-1.emqxsl.com";
const char* mqtt_topic_temperature = "emqx/esp8266";
const char* mqtt_topic_speech = "emqx/speech-to-text";
const char* mqtt_topic_objects = "emqx/objects";
const char* mqtt_username = "chatadoriana";
const char* mqtt_password = "chatadoriana";

// DS18B20 settings
#define ONE_WIRE_BUS 2 // GPIO2 (D4 on NodeMCU)
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// NTP Server settings
const char* ntp_server = "pool.ntp.org";
const long gmt_offset_sec = 0;
const int daylight_offset_sec = 0;

// LCD Configuration
LiquidCrystal_I2C lcd(0x27, 16, 2);

// WiFi and MQTT client initialization
BearSSL::WiFiClientSecure espClient;
PubSubClient mqtt_client(espClient);

// SSL certificate for MQTT broker
static const char ca_cert[]
PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
MIIDrzCCApegAwIBAgIQCDvgVpBCRrGhdWrJWZHHSjANBgkqhkiG9w0BAQUFADBh
MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3
d3cuZGlnaWNlcnQuY29tMSAwHgYDVQQDExdEaWdpQ2VydCBHbG9iYWwgUm9vdCBD
QTAeFw0wNjExMTAwMDAwMDBaFw0zMTExMTAwMDAwMDBaMGExCzAJBgNVBAYTAlVT
MRUwEwYDVQQKEwxEaWdpQ2VydCBJbmMxGTAXBgNVBAsTEHd3dy5kaWdpY2VydC5j
b20xIDAeBgNVBAMTF0RpZ2lDZXJ0IEdsb2JhbCBSb290IENBMIIBIjANBgkqhkiG
9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4jvhEXLeqKTTo1eqUKKPC3eQyaKl7hLOllsB
CSDMAZOnTjC3U/dDxGkAV53ijSLdhwZAAIEJzs4bg7/fzTtxRuLWZscFs3YnFo97
nh6Vfe63SKMI2tavegw5BmV/Sl0fvBf4q77uKNd0f3p4mVmFaG5cIzJLv07A6Fpt
43C/dxC//AH2hdmoRBBYMql1GNXRor5H4idq9Joz+EkIYIvUX7Q6hL+hqkpMfT7P
T19sdl6gSzeRntwi5m3OFBqOasv+zbMUZBfHWymeMr/y7vrTC0LUq7dBMtoM1O/4
gdW7jVg/tRvoSSiicNoxBN33shbyTApOB6jtSj1etX+jkMOvJwIDAQABo2MwYTAO
BgNVHQ8BAf8EBAMCAYYwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQUA95QNVbR
TLtm8KPiGxvDl7I90VUwHwYDVR0jBBgwFoAUA95QNVbRTLtm8KPiGxvDl7I90VUw
DQYJKoZIhvcNAQEFBQADggEBAMucN6pIExIK+t1EnE9SsPTfrgT1eXkIoyQY/Esr
hMAtudXH/vTBH1jLuG2cenTnmCmrEbXjcKChzUyImZOMkXDiqw8cvpOp/2PV5Adg
06O/nVsJ8dWO41P0jmP6P6fbtGbfYmbW0W5BjfIttep3Sp+dWOIrWcBAI+0tKIJF
PnlUkiaY4IBIqDfv8NZ5YBberOgOzW6sRBc4L0na4UU+Krk2U886UAb3LujEV0ls
YSEY1QSteDwsOoBrp+uvFRTp2InBuThs4pFsiv9kuXclVzDAGySj4dzp30d8tbQk
CAUw7C29C79Fv1C5qfPrmAESrciIxpg0X40KPMbp1ZWVbd4=
-----END CERTIFICATE-----
)EOF";

// Function declarations
void connectToWiFi();
void connectToMQTT();
void syncTime();
void publishTemperature();
void callback(char* topic, byte* payload, unsigned int length);

void setup() {
    Serial.begin(115200);

    // Initialize the LCD
    lcd.init(); // Initialize the LCD
    lcd.begin(16, 2);
    lcd.backlight();
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Starting...");

    connectToWiFi();
    syncTime();
    mqtt_client.setServer(mqtt_broker, mqtt_port);
    mqtt_client.setCallback(callback);
    connectToMQTT();
    sensors.begin();

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Ready...");
}

void loop() {
    if (!mqtt_client.connected()) {
        connectToMQTT();
    }
    mqtt_client.loop();

    static unsigned long lastPublishTime = 0;
    if (millis() - lastPublishTime >= 10000) {
        lastPublishTime = millis();
        publishTemperature();
    }
}

void connectToWiFi() {
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("Connected to WiFi. IP: " + WiFi.localIP().toString());
}

void syncTime() {
    configTime(gmt_offset_sec, daylight_offset_sec, ntp_server);
    while (time(nullptr) < 8 * 3600 * 2) {
        delay(1000);
        Serial.print(".");
    }
    Serial.println("Time synchronized");
}

void connectToMQTT() {
    BearSSL::X509List serverTrustedCA(ca_cert);
    espClient.setTrustAnchors(&serverTrustedCA);
    while (!mqtt_client.connected()) {
        String client_id = "esp8266-client-" + String(WiFi.macAddress());
        Serial.printf("Connecting to MQTT Broker as %s...\n", client_id.c_str());
        if (mqtt_client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
            Serial.println("Connected to MQTT broker");
            mqtt_client.subscribe(mqtt_topic_speech);
            mqtt_client.subscribe(mqtt_topic_objects);
        } else {
            char err_buf[128];
            espClient.getLastSSLError(err_buf, sizeof(err_buf));
            Serial.print("Failed to connect to MQTT broker, rc=");
            Serial.println(mqtt_client.state());
            Serial.print("SSL error: ");
            Serial.println(err_buf);
            delay(5000);
        }
    }
}

void publishTemperature() {
    sensors.requestTemperatures();
    float temperatureC = sensors.getTempCByIndex(0);

    if (temperatureC != DEVICE_DISCONNECTED_C) {
        String tempStr = String(temperatureC);
        Serial.printf("Publishing temperature: %.2f°C to topic: %s\n", temperatureC, mqtt_topic_temperature);

        bool success = mqtt_client.publish(mqtt_topic_temperature, tempStr.c_str());
        if (success) {
            Serial.println("Temperature successfully published.");
        } else {
            Serial.println("Failed to publish temperature to MQTT broker.");
        }
    } else {
        Serial.println("Error: Could not read temperature from DS18B20.");
    }
}

void callback(char* topic, byte* payload, unsigned int length) {
    String message;
    for (unsigned int i = 0; i < length; i++) {
        message += (char)payload[i];
    }

    Serial.printf("Message received on topic %s: %s\n", topic, message.c_str());

    if (String(topic) == mqtt_topic_speech) {
        // Clear only the first line
        lcd.setCursor(0, 0);
        lcd.print("                "); // Clear line by printing spaces
        lcd.setCursor(0, 0);
        if (message.length() > 16) {
            lcd.print(message.substring(0, 16));
        } else {
            lcd.print(message);
        }
    } else if (String(topic) == mqtt_topic_objects) {
        // Clear only the second line
        lcd.setCursor(0, 1);
        lcd.print("                "); // Clear line by printing spaces
        lcd.setCursor(0, 1);
        if (message.length() > 16) {
            lcd.print(message.substring(0, 16));
        } else {
            lcd.print(message);
        }
    }
}
