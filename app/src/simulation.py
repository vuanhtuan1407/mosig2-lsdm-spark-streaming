import os
import pandas as pd
import json
import time
import random
from queue import PriorityQueue

import configs
from utils import format_df_to_dict


class TaskEventSimulator:
    def __init__(self):
        self.data = self.__prepare_data()
                        
    def __prepare_data(self):
        schema_dict = json.load(open(configs.SCHEMA_DICT_PATH, "r", encoding="utf-8"))
        file_path = configs.DATA_DIR + "task_events/part-00160-of-00500.csv"
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file for metric 'task_events' not found at path: {file_path}")

        df = pd.read_csv(file_path, header=None)
        data = format_df_to_dict(df, schema_dict['task_events'])
        # data.sort(key=lambda x: x["time"])
        print(f"[INFO] Loaded 'task_events' with {len(data)} records from {file_path}")
        return data

    def stream(self, rate=1):
        task_events = self.data
        n = len(task_events)
        for i in range(n):
            curr = task_events[i]
            yield curr
            print(f"[EMIT] Task event ({curr.get('job_ID')}; {curr.get('machine_ID')}; {curr.get('task_index')}) emitted.")

            # Sleep to simulate real-time processing (apply for all but the last event)
            if i < n - 1:
                nex = task_events[i + 1]
                delta_sec = (nex['time'] - curr['time']) / 1_000_000 / rate
                print(f"[SLEEP] Sleeping for {delta_sec} seconds before processing next event.")
                if delta_sec > 0:
                    time.sleep(delta_sec)


    def stream_jitter(self, rate=1, delay_prob=0.1):
        delay_queue = PriorityQueue(maxsize=1000)
        task_events = self.data

        n = len(task_events)
        for i in range(n):
            curr = task_events[i]

            # Decide whether to delay the current log
            if random.random() < delay_prob and delay_queue.qsize() < delay_queue.maxsize:
                delay_sec = random.uniform(0.0005, 0.001) # Delay between 0.5ms to 1ms
                scheduled_time = time.time() + delay_sec
                delay_queue.put((scheduled_time, curr))
                print(f"[DELAY] Task event ({curr.get('job_ID')}; {curr.get('machine_ID')}; {curr.get('task_index')}) delayed. Queue size: {delay_queue.qsize()}. Delayed time: {delay_sec}")
            else:
                yield curr
                print(f"[EMIT] Task event ({curr.get('job_ID')}; {curr.get('machine_ID')}; {curr.get('task_index')}) emitted.")

            # Check and emit any delayed logs whose time has come (random number per loop)
            now = time.time()
            max_n_delay = random.randint(1, delay_queue.qsize()) if not delay_queue.empty() else 0
            while not delay_queue.empty() and max_n_delay > 0:
                scheduled_time, log = delay_queue.queue[0]  # peek
                if scheduled_time <= now:
                    delay_queue.get()
                    yield log
                    print(f"[EMIT-DELAYED] Task event ({log.get('job_ID')}; {log.get('machine_ID')}; {log.get('task_index')}) emitted after delay.")
                    max_n_delay -= 1
                else:
                    break

            # Sleep to simulate real-time processing (apply for all but the last event)
            if i < n - 1:
                nex = task_events[i + 1]
                delta_sec = (nex['time'] - curr['time']) / 1_000_000 / rate
                print(f"[SLEEP] Sleeping for {delta_sec} seconds before processing next event.")
                if delta_sec > 0:
                    time.sleep(delta_sec)

        # Emit any remaining delayed logs
        while not delay_queue.empty():
            _, log = delay_queue.get()
            yield log
            print(f"[EMIT-DELAYED] Task event ({log.get('job_ID')}; {log.get('machine_ID')}; {log.get('task_index')}) emitted at end.")


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Task Event Simulator")
    parser.add_argument('--rate', type=float, default=1.0, help='Streaming rate (1.0 = real-time)')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    sim = TaskEventSimulator()
    open(configs.LOGS_DIR + "task_events_logs.csv", "w").close()  # Clear previous logs
    for log in sim.stream(rate=args.rate):
        df = pd.DataFrame([log])
        df.to_csv(configs.LOGS_DIR + "task_events_logs.csv", mode='a', header=False, index=False)
        
