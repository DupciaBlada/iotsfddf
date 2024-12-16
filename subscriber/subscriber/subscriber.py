import os
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
import logging
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s - %(filename)s:%(lineno)d'
)
logger = logging.getLogger()

class MQTTConfig:
    BROKER = "h7349222.ala.eu-central-1.emqxsl.com"
    PORT = 8883
    USERNAME = "chatadoriana"
    PASSWORD = "chatadoriana"
    TOPIC = "emqx/esp8266"
    CERT_PATH = "emqxsl-ca.crt"

class InfluxDBConfig:
    URL = "http://influxdb:8086"
    TOKEN = "MON-CZ1fE090xmJQ-e0sdZNgjL8mz3sNTpgRsHlsV14rNVc1kNufRcHuN33c3xl1rrneA1PliyNRrvr88q51Rg=="
    ORG = "my-org"
    BUCKET = "temp-data"

class DataCollector:
    def __init__(self):
        self._init_influxdb()
        self._init_mqtt()

    def _init_influxdb(self):
        try:
            self.influx_client = InfluxDBClient(
                url=InfluxDBConfig.URL,
                token=InfluxDBConfig.TOKEN,
                org=InfluxDBConfig.ORG
            )
            self.write_api = self.influx_client.write_api()
            logger.info("InfluxDB connection established")
        except Exception as e:
            logger.error(f"InfluxDB initialization failed: {e}")
            raise

    def _init_mqtt(self):
        try:
            self.mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311)
            self.mqtt_client.username_pw_set(MQTTConfig.USERNAME, MQTTConfig.PASSWORD)
            self.mqtt_client.tls_set(ca_certs=MQTTConfig.CERT_PATH)

            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_message = self._on_message
            self.mqtt_client.on_disconnect = self._on_disconnect

        except Exception as e:
            logger.error(f"Failed to initialize MQTT client: {e}")
            raise

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            client.subscribe(MQTTConfig.TOPIC)
            logger.info(f"Subscribed to {MQTTConfig.TOPIC}")
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker with code: {rc}")
            try:
                self.mqtt_client.reconnect()
                logger.info("Successfully reconnected to MQTT broker")
            except Exception as e:
                logger.error(f"Failed to reconnect to MQTT broker: {e}")
        else:
            logger.info("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, message):
        try:
            temp = float(message.payload.decode())
            point = Point("temperature") \
                .field("value", temp) \
                .time(datetime.utcnow())
                
            self.write_api.write(
                bucket=InfluxDBConfig.BUCKET,
                record=point
            )
            logger.info(f"Temperature {temp:.2f}°C written to InfluxDB")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def start(self):
        try:
            logger.info(f"Connecting to MQTT Broker: {MQTTConfig.BROKER}:{MQTTConfig.PORT}")
            self.mqtt_client.connect(MQTTConfig.BROKER, MQTTConfig.PORT)
            self.mqtt_client.loop_forever()
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        self.influx_client.close()

if __name__ == "__main__":
    collector = DataCollector()
    collector.start()