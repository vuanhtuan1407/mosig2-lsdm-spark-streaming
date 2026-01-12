import os
import time
from confluent_kafka import Producer

import configs

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:29092")
TOPIC = os.getenv("TOPIC_NAME", "cluster-metrics")
LOG_PATH = os.path.join(configs.LOGS_DIR, "task_events_logs.csv")
READ_INTERVAL = 0.01  # seconds
LOG_INTERVAL = 5  # seconds, in console log every 5 seconds

def delivery_report(err, msg):
    if err is not None:
        print(f"[ERROR] Delivery failed: {err} for message at offset {msg.offset()}")

def tail_f(file_path):
    current_file = None

    while True:
        try:
            # If file not open yet, try to open it
            if current_file is None:
                if os.path.exists(file_path):
                    current_file = open(file_path, "r")
                    current_file.seek(0, os.SEEK_END)  # Start from end
                    print(f"[INFO] Opened log file: {file_path}")
                else:
                    time.sleep(READ_INTERVAL)
                    continue

            # Read new lines
            line = current_file.readline()
            if line:
                yield line.strip()
            else:
                time.sleep(READ_INTERVAL)

        except Exception as e:
            print(f"[ERROR] Error reading file: {e}")
            if current_file:
                current_file.close()
                current_file = None
            time.sleep(READ_INTERVAL)

def run_producer():
    p = Producer({"bootstrap.servers": KAFKA_BROKER})
    print(f"[INFO] Connected to Kafka {KAFKA_BROKER}, producing to '{TOPIC}'")

    batch_count = 0
    last_log_time = time.time()

    try:
        for line in tail_f(LOG_PATH):
            p.produce(TOPIC, value=line.encode("utf-8"), callback=delivery_report)
            batch_count += 1

            # poll to trigger delivery reports
            p.poll(0)

            # log periodically
            now = time.time()
            if now - last_log_time >= LOG_INTERVAL:
                print(f"[INFO] Produced {batch_count} messages so far")
                last_log_time = now

    except KeyboardInterrupt:
        print("[INFO] Stopping producer...")

    finally:
        p.flush()
        print(f"[INFO] Producer flushed remaining messages. Total produced: {batch_count}")

if __name__ == "__main__":
    # wait until log file exists
    while not os.path.exists(LOG_PATH):
        print(f"[WARN] Log file {LOG_PATH} not found, waiting...")
        time.sleep(0.5)

    run_producer()
    