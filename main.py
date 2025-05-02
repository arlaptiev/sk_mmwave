import os
import sys
import argparse

import threading

# Add the project root and sibling directories to PYTHONPATH
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from nodes.radar import init_radar_node
from nodes.phone import listen_to_phone



def main():
    parser = argparse.ArgumentParser(description="Start the mmWave Radar Node.")

    # radar args
    parser.add_argument("--lua",            default='configs/1443_mm_config_continuous.lua', type=str, help="Path to the Lua config file")
    parser.add_argument('--host_ip',        default='192.168.33.30', help='IP address of host.')
    parser.add_argument('--host_data_port', default=4098, type=int, help='Data port of host.')
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    # phone args

    args = parser.parse_args()

    # make radar thread
    print(f"[INFO] Starting radar node with config: {args.lua}")
    radar_thread = threading.Thread(init_radar_node(args, callback=print, verbose=args.verbose)) 

    # make phone thread
    #phone_thread = threading.Thread(listen_to_phone())

    # start all threads
    radar_thread.start()
    #phone_thread.start()




if __name__ == "__main__":
    main()
