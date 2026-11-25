import json, os, time, threading
import paho.mqtt.client as mqtt

NIM = "24831074"
BASE = f"coldstorage/{NIM}/freezer01"
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
TB_HOST = os.getenv("TB_HOST", "localhost")
TB_PORT = int(os.getenv("TB_PORT", "1884"))
TOKEN = os.environ["TB_TOKEN"]
BUFFER_FILE = os.getenv("BUFFER_FILE", "buffer.jsonl")
THRESHOLD = -15.0
WINDOW = 60  # detik

lock = threading.Lock()
window, window_start, above = [], time.time(), False

# ---------- ThingsBoard (cloud) ----------
tb = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{NIM}-edge-tb")
tb.username_pw_set(TOKEN)
tb.reconnect_delay_set(1, 10)

def send(values, ts_ms):
    item = {"ts": ts_ms, "values": values}
    with lock:
        if tb.is_connected():
            if tb.publish("v1/devices/me/telemetry", json.dumps(item), qos=1).rc == 0:
                print("[SEND]", values)
                return
        with open(BUFFER_FILE, "a") as f:
            f.write(json.dumps(item) + "\n")
        print("[BUFFER] cloud putus, disimpan:", values)

def flush_buffer():
    with lock:
        if not os.path.exists(BUFFER_FILE):
            return
        with open(BUFFER_FILE) as f:
            lines = [l.strip() for l in f if l.strip()]
        if not lines:
            return
        print(f"[FORWARD] mengirim {len(lines)} data tertunda")
        for l in lines:
            tb.publish("v1/devices/me/telemetry", l, qos=1)
        open(BUFFER_FILE, "w").close()

def tb_on_connect(c, u, f, rc, p):
    print("[TB] connect:", rc)
    c.subscribe("v1/devices/me/attributes", qos=1)
    flush_buffer()

def tb_on_disconnect(c, u, f, rc, p):
    print("[TB] terputus:", rc)

def tb_on_message(c, u, msg):
    data = json.loads(msg.payload)
    data = data.get("shared", data)
    if "fan_on" in data:
        out = json.dumps({"fan_on": bool(data["fan_on"])})
        src.publish(f"{BASE}/cmd/fan", out, qos=1)
        print("[CMD] kipas:", out)

tb.on_connect, tb.on_disconnect, tb.on_message = tb_on_connect, tb_on_disconnect, tb_on_message

# ---------- Mosquitto (lokal) ----------
src = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{NIM}-edge-src")

def on_connect(c, u, f, rc, p):
    print("[MOSQ] connect:", rc)
    c.subscribe(f"{BASE}/temperature")

def on_message(c, u, msg):
    global window, window_start, above
    d = json.loads(msg.payload)
    now = time.time()
    t = d["temperature"]
    window.append(d)

    # deteksi ambang lokal: kirim segera saat melewati batas
    if t > THRESHOLD and not above:
        above = True
        print("[EDGE] ambang terlewati:", t)
        send({"temperature": t, "edge_alert": 1}, int(now * 1000))
    elif t <= THRESHOLD and above:
        above = False
        send({"temperature": t, "edge_alert": 0}, int(now * 1000))

    # agregasi per 1 menit
    if now - window_start >= WINDOW:
        temps = [x["temperature"] for x in window]
        hums = [x["humidity"] for x in window]
        values = {
            "temperature": round(sum(temps) / len(temps), 2),
            "temp_min": min(temps), "temp_max": max(temps),
            "humidity": round(sum(hums) / len(hums), 1),
            "door_open": 1 if any(x["door"] == "open" for x in window) else 0,
            "fan_on": 1 if window[-1].get("fan") == "on" else 0,
            "samples": len(window),
        }
        send(values, int(now * 1000))
        window, window_start = [], now

src.on_connect, src.on_message = on_connect, on_message

tb.connect_async(TB_HOST, TB_PORT, 60)
tb.loop_start()
src.connect(MQTT_HOST, 1883, 60)
src.loop_forever()