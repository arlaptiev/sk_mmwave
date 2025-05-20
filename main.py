import os
import sys
import argparse

import threading

# Add the project root and sibling directories to PYTHONPATH
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from nodes.radar import Radar
from nodes.lidar import listen_to_phone


# radar_buf = [{'data': frame_data, 'node': 'radar', 'timestamp': timestamp}]
radar_buf = [None] * 10000

# is called when the TCP packet from phone arrives
def check_the_box(phone_lidar_msg, phone_socket):
    # phone_lidar_msg: {'data': lidar_frame_data, 'node': 'lidar', 'timestamp': timestamp}
    # checks radar buffer for the correct frame
        # go through the radar_buf and find the closest record 
    # calls detection function
    # sends a response to phone
    pass


def add_to_buf(radar_msg):
    radar_buf.pop(0)
    radar_buf.append(radar_msg)


def main():
    parser = argparse.ArgumentParser(description="Start the mmWave Radar Node.")

    # radar args
    parser.add_argument("--cfg",            default='configs/1443_mmwavestudio_config_continuous.lua', type=str, help="Path to the Lua config file")
    parser.add_argument('--host_ip',        default='192.168.33.30', help='IP address of host.')
    parser.add_argument('--host_data_port', default=4098, type=int, help='Data port of host.')
    # phone args

    args = parser.parse_args()

    # make radar thread
    radar = Radar(args)
    radar_thread = threading.Thread(radar.run_polling(callback=print)) 

    # make phone thread
    #phone_thread = threading.Thread(listen_to_phone(callback=check_the_box))

    # start all threads
    # radar_thread.start()
    #phone_thread.start()






if __name__ == "__main__":
    main()
