from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable, KafkaError
import json
import time
import os
import sys

sys.stdout.reconfigure(line_buffering=True)

print("Producer container started!", flush=True)
print("Python version:", sys.version, flush=True)
print("Current working directory:", os.getcwd(), flush=True)

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

print(f"Using Kafka bootstrap servers: {BOOTSTRAP_SERVERS}", flush=True)

while True:
    try:
        producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')        )
        print("Kafka Producer connected.", flush=True)
        break
    except NoBrokersAvailable:
        print("Kafka not available. Retrying in 5 seconds...", flush=True)
        time.sleep(5)

topic = 'employee-data'

employees = [
    {"emp_id": "E201", "name": "Raj Verma", "department": "Sales", "salary": 60000, "location": "Mumbai"},
    {"emp_id": "E202", "name": "Sara Thomas", "department": "HR", "salary": 55000, "location": "Delhi"},
    {"emp_id": "E203", "name": "Karan Patel", "department": "Engineering", "salary": 72000, "location": "Pune"},
    {"emp_id": "E204", "name": "Anjali Rao", "department": "Finance", "salary": 68000, "location": "Hyderabad"},
    {"emp_id": "E205", "name": "Vikram Singh", "department": "Support", "salary": 52000, "location": "Kolkata"}
]

while True:
    print("\nSending batch of employee records to Kafka...\n", flush=True)
    for emp in employees:
        emp["timestamp"] = time.time()
        future = producer.send(topic, value=emp)
        try:
            record_metadata = future.get(timeout=10)
            print(f"Sent: {emp['emp_id']} | Offset: {record_metadata.offset}", flush=True)
        except KafkaError as e:
            print(f"Failed to send {emp['emp_id']}: {e}", flush=True)
        time.sleep(1)  # simulate stream delay

    print("Sleeping before next batch...\n", flush=True)
    time.sleep(30)


