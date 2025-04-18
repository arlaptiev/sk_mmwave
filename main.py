import os
import sys
import argparse

# Add the project root and sibling directories to PYTHONPATH
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from nodes.radar import init_radar_node






def main():
    parser = argparse.ArgumentParser(description="Start the mmWave Radar Node.")

    # radar args
    parser.add_argument("lua", type=str, help="Path to the Lua config file")
    parser.add_argument('--host_ip',        default='192.168.33.30', help='IP address of host.')
    parser.add_argument('--host_data_port', default=4098, type=int, help='Data port of host.')
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    # phone args

    args = parser.parse_args()

    # Start the radar node
    print(f"[INFO] Starting radar node with config: {args.lua}")
    init_radar_node(args, callback=print, verbose=args.verbose)

    # Start the phone node




if __name__ == "__main__":
    main()
