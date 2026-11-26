# UTS IoT Platform: Monitoring Cold Storage UMKM (FATHAN SHALAHUDDIN AVICENA NIM 24.83.1074)

Studi kasus: cold storage UMKM (suhu, kelembapan, status pintu).
Simulator Python (paho-mqtt) -> Mosquitto -> edge (Docker) -> ThingsBoard CE, plus bridge MQTT -> Kafka.

## Isi repo
- `simulator.py`: simulator sensor freezer01 (jalan di laptop)
- `edge.py`: edge (rata-rata 1 menit, ambang lokal, store and forward, relay perintah kipas)
- `kafka_bridge.py`: bridge MQTT ke Apache Kafka (2 partition)
- `Dockerfile`, `docker-compose.yml`: Mosquitto, edge, Kafka, kafka-bridge
- `mosquitto.conf`: konfigurasi broker (lab lokal)
- `ThingsBoard/docker-compose.yml`: ThingsBoard CE + PostgreSQL

## Prasyarat
Docker Desktop, Python 3, dan `pip install paho-mqtt`.

## Cara menjalankan
1. **ThingsBoard** (sekali di awal):
   ```
   cd ThingsBoard
   docker compose run --rm -e INSTALL_TB=true -e LOAD_DEMO=true thingsboard-ce
   docker compose up -d
   ```
   Buka http://localhost:8080 (akun demo tenant), buat device `24831074-freezer01`, salin access token.
2. **Token:** salin `.env.example` menjadi `.env`, isi `TB_TOKEN`. Jangan commit `.env`.
3. **Mosquitto, edge, Kafka:**
   ```
   docker compose up -d --build
   ```
4. **Topic Kafka dengan 2 partition** (buat sebelum data masuk, atau ubah dengan `--alter`):
   ```
   docker exec kafka-24831074 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --topic coldstorage.24831074.telemetry --partitions 2 --replication-factor 1
   ```
5. **Simulator:** `python simulator.py`
6. **Dua consumer** dalam satu group (di dua terminal):
   ```
   docker exec -it kafka-24831074 /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic coldstorage.24831074.telemetry --group cold-group-24831074 --property print.key=true --property print.partition=true
   ```
7. **Perintah ke perangkat:** di ThingsBoard, tambahkan shared attribute `fan_on` (boolean) pada device.

## Catatan keamanan
Token, password, dan API key tidak disimpan di repo. Password database dan akun demo ThingsBoard hanya untuk percobaan lokal.
