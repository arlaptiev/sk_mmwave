import os
import sys
import argparse

import threading

# Add the project root and sibling directories to PYTHONPATH
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from nodes.radar import Radar
from nodes.phone import Phone



RADAR_BUF_SIZE = 10000
PHONE_BUF_SIZE = 100

radar_buf = [None] * RADAR_BUF_SIZE                     # [{'data': frame_data, 'node': 'radar', 'timestamp': timestamp}]    
phone_buf = [None] * PHONE_BUF_SIZE                     # [{'data': lidar_frame_data, 'node': 'phone', 'timestamp': timestamp}]



def detect_object(phone_msg, phone_socket):
    # phone_msg: {'data': lidar_frame_data, 'node': 'phone', 'timestamp': timestamp}
    # TODO: implement detection + response to phone

    # checks radar buffer for the correct frame
        # go through the radar_buf and find the closest record 
    # calls detection function
    # sends a response to phone
    pass




def handle_phone_msg(phone_msg, phone_socket):
    """Called when a new phone reading TCP packet is received. Adds a new phone message to the phone buffer."""
    phone_buf.pop(0)
    phone_buf.append(phone_msg)

    detect_object(phone_msg, phone_socket)


def handle_radar_msg(radar_msg):
    """Called when a new radar reading is passed over the Ethernet. Adds a new radar message to the radar buffer."""
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

    # Start the radar node
    radar = Radar(args)
    radar_thread = threading.Thread(radar.run_polling(callback=print)) 

    # Start the phone node
    phone = Phone()
    phone_thread = threading.Thread(phone.run_polling(callback=print))


    # Start all threads
    radar_thread.start()
    phone_thread.start()






if __name__ == "__main__":
    main()
