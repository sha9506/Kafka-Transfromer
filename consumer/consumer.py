from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable, KafkaError
from pymongo import MongoClient
import json
import time
import os
import sys

sys.stdout.reconfigure(line_buffering=True)

print("Consumer container started!", flush=True)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:example@mongodb:27017")

print(f"Kafka bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}", flush=True)
print(f"MongoDB URI: {MONGO_URI}", flush=True)

consumer = None
retry_count = 0
max_retries = 30

while consumer is None and retry_count < max_retries:
    try:
        consumer = KafkaConsumer(
            'employee-data',
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='employee-consumer-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            consumer_timeout_ms=1000
        )
        print("Kafka Consumer connected successfully!", flush=True)
        break
    except NoBrokersAvailable:
        retry_count += 1
        print(f"Kafka not available (attempt {retry_count}/{max_retries}). Retrying in 5 seconds...", flush=True)
        time.sleep(5)
    except Exception as e:
        retry_count += 1
        print(f"Error connecting to Kafka (attempt {retry_count}/{max_retries}): {e}", flush=True)
        time.sleep(5)

if consumer is None:
    print("Failed to connect to Kafka after maximum retries. Exiting.", flush=True)
    sys.exit(1)

mongo_client = None
retry_count = 0

while mongo_client is None and retry_count < max_retries:
    try:
        mongo_client = MongoClient(MONGO_URI)        # Test the connection
        mongo_client.admin.command('ping')
        print("MongoDB connected successfully!", flush=True)
        break
    except Exception as e:
        retry_count += 1
        print(f"MongoDB not available (attempt {retry_count}/{max_retries}): {e}. Retrying in 5 seconds...", flush=True)
        time.sleep(5)

if mongo_client is None:
    print("Failed to connect to MongoDB after maximum retries. Exiting.", flush=True)
    sys.exit(1)

raw_db = mongo_client["raw_employee_db"]
raw_collection = raw_db["employees"]

print("Consumer started and ready to process messages...", flush=True)

try:
    for message in consumer:
        try:
            data = message.value
            data['status'] = 'received'
            data['processed_at'] = time.time()
            
            result = raw_collection.insert_one(data)
            print(f"Inserted employee {data.get('emp_id', 'unknown')} into raw_employee_db.employees (ID: {result.inserted_id})", flush=True)
            
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON message: {e}", flush=True)
        except Exception as e:
            print(f"Error processing message: {e}", flush=True)
            
except KeyboardInterrupt:
    print("Consumer interrupted by user", flush=True)
except Exception as e:
    print(f"Fatal error in consumer: {e}", flush=True)
finally:
    if consumer:
        consumer.close()
        print("Kafka consumer closed", flush=True)
    if mongo_client:
        mongo_client.close()
        print("MongoDB connection closed", flush=True)
