import json, os, uuid
import paho.mqtt.client as mqtt

TOKEN = os.environ["TB_TOKEN"]
NIM = "24831074"
uid = uuid.uuid4().hex[:6]

# --- ThingsBoard ---
def tb_on_connect(client, userdata, flags, reason_code, properties):
    print("[TB] connect:", reason_code)
    client.subscribe("v1/devices/me/attributes", qos=1)

def tb_on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    data = data.get("shared", data)
    if "fan_on" in data:
        out = json.dumps({"fan_on": bool(data["fan_on"])})
        src.publish(f"coldstorage/{NIM}/freezer01/cmd/fan", out, qos=1)
        print("[CMD] shared attribute -> kipas:", out)

tb = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{NIM}-tb-{uid}")
tb.username_pw_set(TOKEN)
tb.on_connect = tb_on_connect
tb.on_message = tb_on_message
tb.connect("localhost", 1884, 60)
tb.loop_start()

# --- Mosquitto ---
def on_connect(client, userdata, flags, reason_code, properties):
    print("[MOSQ] connect:", reason_code)
    client.subscribe(f"coldstorage/{NIM}/freezer01/temperature")

def on_message(client, userdata, msg):
    d = json.loads(msg.payload)
    telemetry = {
        "temperature": d["temperature"],
        "humidity": d["humidity"],
        "door_open": 1 if d["door"] == "open" else 0,
        "fan_on": 1 if d.get("fan") == "on" else 0,
    }
    tb.publish("v1/devices/me/telemetry", json.dumps(telemetry), qos=1)
    print("diteruskan:", telemetry)

src = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{NIM}-src-{uid}")
src.on_connect = on_connect
src.on_message = on_message
src.connect("localhost", 1883, 60)
src.loop_forever()