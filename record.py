import os
import sys
import argparse
import pickle
from datetime import datetime

import threading

# Add the project root and sibling directories to PYTHONPATH
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from nodes.radar import Radar
from nodes.phone import Phone


# Global session timestamp and node directory map
recording_start_time = datetime.now().strftime("%Y%m%d_%H%M%S")
base_dir = os.path.join("data", "recordings", recording_start_time)

node_dirs = {}

def setup_logging_dir(node_name):
    node_path = os.path.join(base_dir, node_name)
    os.makedirs(node_path, exist_ok=True)
    node_dirs[node_name] = node_path
    print(f"[INFO] Logging {node_name} data to {node_path}")


def record(message):
    node = message.get("node", "unknown")
    if node not in node_dirs:
        print(f"[WARN] No directory initialized for node '{node}'. Skipping.")
        return

    # Use full ISO timestamp with underscores instead of colons
    timestamp = datetime.now().isoformat().replace(":", "-")
    file_path = os.path.join(node_dirs[node], f"{timestamp}.pkl")

    with open(file_path, "wb") as f:
        pickle.dump(message, f)

    print(f"[DEBUG] Saved {node} message to {file_path}")


def main():
    parser = argparse.ArgumentParser(description="Start the mmWave Radar Node.")

    # radar args
    parser.add_argument("--cfg",            default='configs/1443_mmwavestudio_config_continuous.lua', type=str, help="Path to the Lua config file")
    parser.add_argument('--host_ip',        default='192.168.33.30', help='IP address of host.')
    parser.add_argument('--host_data_port', default=4098, type=int, help='Data port of host.')
    # phone args

    args = parser.parse_args()

    # Start the radar node
    setup_logging_dir("radar")
    radar = Radar(args.cfg, args.host_ip, args.host_data_port)
    radar_thread = threading.Thread(radar.run_polling(callback=record)) 

    # Start the phone node
    setup_logging_dir("phone")
    phone = Phone()
    phone_thread = threading.Thread(phone.run_polling(callback=record))


    # Start all threads
    radar_thread.start()
    phone_thread.start()


if __name__ == "__main__":
    main()
