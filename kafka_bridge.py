import json, os
import paho.mqtt.client as mqtt
from confluent_kafka import Producer

NIM = "24831074"
TOPIC = f"coldstorage.{NIM}.telemetry"
PARTITION = {"temperature": 0, "humidity": 1, "door": 1}

producer = Producer({"bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")})

def on_connect(c, u, f, rc, p):
    print("[MOSQ] connect:", rc)
    c.subscribe(f"coldstorage/{NIM}/freezer01/+")

def on_message(c, u, msg):
    sensor = msg.topic.split("/")[-1]
    if sensor not in PARTITION:
        return
    producer.produce(TOPIC, key=sensor, value=msg.payload,
                     partition=PARTITION[sensor])
    producer.poll(0)
    print(f"[KAFKA] {sensor} -> partition {PARTITION[sensor]}")

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{NIM}-kafka-bridge")
c.on_connect, c.on_message = on_connect, on_message
c.connect(os.getenv("MQTT_HOST", "localhost"), 1883, 60)
c.loop_forever()