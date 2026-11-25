FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir paho-mqtt confluent-kafka
COPY edge.py kafka_bridge.py ./
CMD ["python", "-u", "edge.py"]