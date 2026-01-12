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
        file_path = configs.DATA_DIR + "task_events/part-00161-of-00500.csv"
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
            curr = task_events[i].copy() 
            curr['time'] = int(time.time() * 1_000) # milliseconds
            
            yield curr
            print(f"[EMIT] Task event ({curr.get('job_ID')}; {curr.get('machine_ID')}; {curr.get('task_index')}) emitted at {curr['time']}.")
            
            # Sleep to simulate real-time processing (apply for all but the last event)
            if i < n - 1:
                nex = task_events[i + 1]
                
                delta_microsec = (nex['time'] - task_events[i]['time'])
                print(f"[INFO] Original interval between events: {delta_microsec} microseconds.")
                delta_sec = delta_microsec / 1_000_000
                
                # Cap intervals greater than 2 seconds to random value between 1-2s
                if delta_sec > 2:
                    delta_sec = random.uniform(1, 2)
                    print(f"[SLEEP] Original interval > 2s, capped to {delta_sec:.3f} seconds.")
                else:
                    delta_sec = delta_sec * 1_000 # Scale interval to milliseconds
                    print(f"[SLEEP] Adjusted interval to {delta_sec:.3f} milliseconds.")    
                
                # Apply rate adjustment
                delta_sec = delta_sec / rate
                
                print(f"[SLEEP] Sleeping for {delta_sec:.3f} seconds before processing next event.")
                if delta_sec > 0:
                    time.sleep(delta_sec)

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Task Event Simulator")
    parser.add_argument('--rate', type=float, default=1.0, help='Streaming rate (1.0 = real-time)')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    sim = TaskEventSimulator()
    for log in sim.stream(rate=args.rate):
        df = pd.DataFrame([log])
        df.to_csv(configs.LOGS_DIR + "task_events_logs.csv", mode='a', header=False, index=False)
        
