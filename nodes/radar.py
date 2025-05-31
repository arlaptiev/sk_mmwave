#!/usr/bin/env python3

"""Simple publisher of raw radar data, without ROS dependency."""

import os
import sys
import time
from datetime import datetime
import argparse
import numpy as np

from src.xwr_raw.dcapub import DCAPub
from src.xwr_raw.dsp import reshape_frame


class Radar:
    def __init__(self, cfg='configs/1443_mmwavestudio_config_continuous.lua', host_ip='192.168.33.30', host_data_port=4098):
        """Initializes radar capture and starts publishing frames.

        Args:
            cfg (str): Path to the LUA configuration file for radar.
            host_ip (str): IP address of the host to connect to.
            host_data_port (int): Data port of the host to connect to.
        """
        print(f"[INFO] Starting radar node with config: {cfg}")
        print(f"[INFO] Connecting radar with host {host_ip}:{host_data_port}")

        self.dcapub = DCAPub(
            cfg=cfg,
            host_ip=host_ip,
            host_data_port=int(host_data_port)
        )

        self.config = self.dcapub.config
        self.params = self.dcapub.params
        print("[INFO] Radar connected. Params:")
        print(self.dcapub.config)

    def run_polling(self, callback=None, lose_frames=False):
        print("[INFO] Starting data capture...")
        
        # flush the data buffer
        self.dcapub.dca1000.flush_data_socket()

        try:
            while True:
                raw_frame_data, new_frame = self.dcapub.update_frame_buffer()
                if new_frame:
                    # NOTE: this timestamp is python application-level timestamp. Is  different 
                    # from harware-level kernel timestamps. Can try to get hardware timestamps (but works only on Linux)
                    timestamp = datetime.now()
                    frame_data = reshape_frame(raw_frame_data, self.params['n_chirps'], self.params['n_samples'], self.params['n_rx'])

                    # frame_data is shaped as (n_chirps, n_samples, n_rx)
                    radar_msg = {'data': frame_data, 'node': 'radar', 'timestamp': timestamp, 'params': self.params}

                    if callback:
                        callback(radar_msg)

                    if lose_frames:
                       self.dcapub.dca1000.flush_data_socket() 

        except KeyboardInterrupt:
            self.close()
            del self
            print("[INFO] Stopping radar capture.")


    def read(self):
        """Reads a single full frame of radar data."""
        discared_incomplete = False

        # flush the data buffer
        self.dcapub.dca1000.flush_data_socket()

        try:
            while True:
                raw_frame_data, new_frame = self.dcapub.update_frame_buffer()
                if new_frame:
                    # discard incomplete frame
                    if not discared_incomplete:
                        discared_incomplete = True
                    else:
                        frame_data = reshape_frame(raw_frame_data, self.params['n_chirps'], self.params['n_samples'], self.params['n_rx'])
                        return frame_data

        except KeyboardInterrupt:
            print("[INFO] Stopping frame capture.")


    def flush(self):
        # flush the data buffer
        self.dcapub.dca1000.flush_data_socket()

    
    def close(self):
        self.dcapub.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run radar data publisher without ROS.")
    parser.add_argument('--cfg',            default='configs/1443_mmwavestudio_config_continuous.lua', help="Path to LUA configuration file for radar")
    parser.add_argument('--host_ip',        default='192.168.33.30', help='IP address of host.')
    parser.add_argument('--host_data_port', default=4098, type=int, help='Data port of host.')
    args = parser.parse_args()

    # Use a simple print function as default publisher for CLI runs
    radar = Radar(args.cfg, args.host_ip, args.host_data_port)

    try:
        radar.run_polling(callback=print)
    except KeyboardInterrupt:
        print("[INFO] Shutting down radar node.")
    finally:
        radar.close()



