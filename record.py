import os
import sys
import argparse
import csv
from datetime import datetime
import json
import numpy as np


# Add the project root and sibling directories to PYTHONPATH
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from nodes.radar import init_radar_node




# Global writer map
writers = {}

def setup_logging_file(node_name, cols):
    dir_path = os.path.join("data", node_name)
    os.makedirs(dir_path, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{node_name}_{timestamp}.csv"
    file_path = os.path.join(dir_path, filename)

    file = open(file_path, "w", newline="")
    writer = csv.DictWriter(file, fieldnames=cols)
    writer.writeheader()

    writers[node_name] = (file, writer)
    print(f"[INFO] Logging {node_name} data to {file_path}")



def serialize(value):
    if isinstance(value, (np.ndarray, list, tuple)):
        return json.dumps(value.tolist())  # cleaner and CSV-safe
    elif isinstance(value, dict):
        return json.dumps(value)
    else:
        return value



def record(message):
    node = message.get("node", "unknown")

    if node not in writers:
        print(f"[WARN] No file initialized for node '{node}'. Skipping.")
        return

    _, writer = writers[node]

    serialized_message = {k: serialize(v) for k, v in message.items()}
    writer.writerow(serialized_message)




def main():
    parser = argparse.ArgumentParser(description="Start the mmWave Radar Node.")

    # radar args
    parser.add_argument("--cfg",            default='configs/1443_mmwavestudio_config_continuous.lua', type=str, help="Path to the Lua config file")
    parser.add_argument('--host_ip',        default='192.168.33.30', help='IP address of host.')
    parser.add_argument('--host_data_port', default=4098, type=int, help='Data port of host.')
    # phone args

    args = parser.parse_args()

    # Start the radar node
    setup_logging_file("radar", ['node', 'data', 'timestamp'])
    Radar(args, callback=record)

    # Start the phone node




if __name__ == "__main__":
    main()
