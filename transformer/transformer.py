from pymongo import MongoClient, ReturnDocument
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
import time
import os
import sys

sys.stdout.reconfigure(line_buffering=True)

print("Transformer container started", flush=True)
print("Python version:", sys.version, flush=True)
print("Current working directory:", os.getcwd(), flush=True)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:example@mongodb:27017/")
POD_NAME = os.getenv("POD_NAME", "transformer-unknown")
MAX_RETRIES = 3

print(f"Pod Name: {POD_NAME}", flush=True)
print(f"MongoDB URI: {MONGO_URI}", flush=True)

client = None
while client is None:
    try:
        print("Attempting to connect to MongoDB...", flush=True)
        client = MongoClient(MONGO_URI)
        client.admin.command('ping')  # test connection
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

def get_latency_bucket(seconds):
    if seconds < 2:
        return "low"
    elif seconds < 5:
        return "medium"
    return "high"

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
            "transformed_by": POD_NAME,
            "region": data.get("region", "unknown")
        }
    except Exception as e:
        raise ValueError(f"Transformation failed: {e}")

def process_received_employees():
    print("Starting to monitor for new employee data...", flush=True)

    while True:
        try:
            doc = raw_collection.find_one_and_update(
                {
                    "status": "received",
                    "retry_count": {"$lt": MAX_RETRIES}
                },
                {
                    "$set": {
                        "status": "processing",
                        "locked_by": POD_NAME,
                        "locked_at": datetime.utcnow()
                    },
                    "$inc": {"retry_count": 1},
                    "$push": {"audit": f"Locked by {POD_NAME} at {datetime.utcnow().isoformat()}"}
                },
                sort=[("priority", 1), ("timestamp", 1)],
                return_document=ReturnDocument.BEFORE
            )

            if not doc:
                print("No new employee data. Sleeping...", flush=True)
                time.sleep(5)
                continue

            emp_id = doc.get("emp_id", doc["_id"])
            print(f"Picked for processing: {emp_id}", flush=True)
            start_time = time.time()

            try:
                transformed = transform_employee(doc)
                processed_collection.insert_one(transformed)

                end_time = time.time()
                processing_duration = round(end_time - start_time, 2)
                latency = get_latency_bucket(processing_duration)

                raw_collection.update_one(
                    {"_id": doc["_id"]},
                    {
                        "$set": {
                            "status": "completed",
                            "processed_at": datetime.utcnow(),
                            "processing_time": processing_duration,
                            "latency_bucket": latency,
                            "transformed_by": POD_NAME
                        },
                        "$unset": {"locked_by": "", "locked_at": ""},
                        "$push": {"audit": f"Completed by {POD_NAME} in {processing_duration}s"}
                    }
                )
                print(f"Processed: {emp_id} in {processing_duration}s", flush=True)

            except Exception as e:
                error_msg = str(e)
                print(f"Failed: {emp_id} | {error_msg}", flush=True)

                raw_collection.update_one(
                    {"_id": doc["_id"]},
                    {
                        "$set": {
                            "status": "failed",
                            "error_reason": error_msg,
                            "failed_at": datetime.utcnow()
                        },
                        "$unset": {"locked_by": "", "locked_at": ""},
                        "$push": {"audit": f"Failed by {POD_NAME}: {error_msg}"}
                    }
                )

            time.sleep(1)

        except Exception as e:
            print(f"Error in processing loop: {e}. Retrying in 10 seconds...", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    print("Starting employee transformer...", flush=True)
    process_received_employees()
