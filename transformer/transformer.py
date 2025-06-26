from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
import time
import os
import sys

sys.stdout.reconfigure(line_buffering=True)

print("Transformer container started!", flush=True)
print("Python version:", sys.version, flush=True)
print("Current working directory:", os.getcwd(), flush=True)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:example@mongodb:27017/")
POD_NAME = os.getenv("POD_NAME", "transformer-unknown")

print(f"Pod Name: {POD_NAME}", flush=True)
print(f"MongoDB URI: {MONGO_URI}", flush=True)

client = None
while client is None:
    try:
        print("Attempting to connect to MongoDB...", flush=True)
        client = MongoClient(MONGO_URI)
        client.admin.command('ping')
        print("MongoDB connection established!", flush=True)
        break
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"MongoDB not available: {e}. Retrying in 5 seconds...", flush=True)
        time.sleep(5)
    except Exception as e:
        print(f"Unexpected error connecting to MongoDB: {e}. Retrying in 5 seconds...", flush=True)
        time.sleep(5)

raw_db = client["raw_employee_db"]
raw_collection = raw_db["employees"]

processed_db = client["processed_employee_db"]
processed_collection = processed_db["employees"]

def transform_employee(data):
    try:
        salary_raw = data.get('salary', 0)
        salary = float(salary_raw)

        return {
            "emp_id": data.get("emp_id", "N/A"),
            "name": str(data.get("name", "Unknown")).title(),
            "department": str(data.get("department", "N/A")).upper(),
            "annual_salary": f"{salary:,.2f} INR",
            "location": str(data.get("location", "N/A")).title(),
            "processed_at": datetime.utcnow(),
            "status": "completed",
            "raw_data": data,  # Raw document trace
            "audit": {
                "processed_by": POD_NAME,
                "processed_at": datetime.utcnow()
            }
        }

    except Exception as e:
        raise ValueError(f"Transformation failed: {e}")

def process_received_employees():
    print("Starting to monitor for new employee data...", flush=True)
    
    while True:
        try:
            docs = list(raw_collection.find({"status": "received"}))

            if not docs:
                print("No new employee data. Sleeping...", flush=True)
                time.sleep(5)
                continue

            print(f"Found {len(docs)} new employee records to process", flush=True)

            for doc in docs:
                try:
                    transformed = transform_employee(doc)
                    processed_collection.insert_one(transformed)

                    raw_collection.update_one(
                        {"_id": doc["_id"]},
                        {
                            "$set": {
                                "status": "completed",
                                "processed_by": POD_NAME,
                                "processed_at": datetime.utcnow(),
                                "audit.processed_by": POD_NAME,
                                "audit.processed_at": datetime.utcnow()
                            }
                        }
                    )
                    print(f"Processed: {doc.get('emp_id', doc['_id'])} at {datetime.utcnow()}", flush=True)

                except Exception as e:
                    error_msg = str(e)
                    print(f"Failed: {doc.get('emp_id', doc['_id'])} | Error: {error_msg}", flush=True)

                    raw_collection.update_one(
                        {"_id": doc["_id"]},
                        {
                            "$set": {
                                "status": "failed",
                                "error_reason": error_msg,
                                "audit.failed_by": POD_NAME,
                                "audit.failed_at": datetime.utcnow(),
                                "raw_data": doc
                            }
                        }
                    )

            time.sleep(2)
            
        except Exception as e:
            print(f"Error in processing loop: {e}. Retrying in 10 seconds...", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    print("Starting employee transformer...", flush=True)
    process_received_employees()
