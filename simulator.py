import json, random, time
from datetime import datetime, timezone, timedelta
import paho.mqtt.client as mqtt

NIM = "24831074"
DEVICE = f"{NIM}-freezer01"
BASE = f"coldstorage/{NIM}/freezer01"
fan_on = False

def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe(f"{BASE}/cmd/fan", qos=1)

def on_message(client, userdata, msg):
    global fan_on
    cmd = json.loads(msg.payload)
    fan_on = bool(cmd.get("fan_on"))
    print(f">>> PERINTAH DITERIMA: kipas {'ON' if fan_on else 'OFF'}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=DEVICE)
client.will_set(f"{BASE}/status", "offline", qos=1, retain=True)
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_start()
client.publish(f"{BASE}/status", "online", qos=1, retain=True)

temp, door = -18.0, "closed"
while True:
    if random.random() < 0.1:
        door = "open" if door == "closed" else "closed"
    target = -12.0 if door == "open" else -18.0
    if fan_on:
        target -= 6
    temp += (target - temp) * 0.2 + random.uniform(-0.3, 0.3)
    hum = round(random.uniform(60, 75), 1)
    ts = datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="seconds")
    payload = {"device_id": DEVICE, "ts": ts,
               "temperature": round(temp, 1), "humidity": hum,
               "door": door, "fan": "on" if fan_on else "off"}
    client.publish(f"{BASE}/temperature", json.dumps(payload), qos=0)
    client.publish(f"{BASE}/humidity", json.dumps(payload), qos=0)
    client.publish(f"{BASE}/door", json.dumps(payload), qos=1, retain=True)
    print(payload)
    time.sleep(5)