#!/usr/bin/env python3

"""Simple publisher of raw radar data, without ROS dependency."""

import os
import sys
import time
from datetime import datetime
import argparse
import numpy as np

from xwr_raw.dcapub import DCAPub
from xwr_raw.dsp import reshape_frame


class Radar:
    def __init__(self, args, callback=None):
        """Initializes radar capture and starts publishing frames.

        Args:
            args: Parsed arguments with:
                `cfg`           - Path to LUA configuration file for radar
                `host_ip`       - IP address of host
                `host_port`     - Data port of host
            callback (callable, optional): Function to handle published radar data.
            verbose (bool): If True, prints status messages.
        """
        print(f"[INFO] Starting radar node with config: {args.cfg}")
        print(f"[INFO] Connecting radar with host {args.host_ip}:{args.host_data_port}")

        self.dca = DCAPub(
            cfg=args.cfg,
            host_ip=args.host_ip,
            host_data_port=int(args.host_data_port)
        )

        self.params = self.dca.params
        print("[INFO] Radar params:")
        for p in self.params:
            print(p, ':', self.params[p])

        self.callback = callback

    def run_polling(self):
        print("[INFO] Radar connected. Starting data capture...")
        try:
            while True:
                raw_frame_data, new_frame = self.dca.update_frame_buffer()
                if new_frame:
                    # NOTE: this timestamp is python application-level timestamp. Is  different 
                    # from harware-level kernel timestamps. Can try to get hardware timestamps (but works only on Linux)
                    timestamp = datetime.now()
                    frame_data = reshape_frame(raw_frame_data, self.params['n_chirps'], self.params['n_samples'], self.params['n_rx'])
                    radar_msg = {'data': frame_data, 'node': 'radar', 'timestamp': timestamp}

                    if self.callback:
                        self.callback(radar_msg)

                # time.sleep(0.01)  # Prevents busy-looping
        except KeyboardInterrupt:
            print("[INFO] Stopping radar capture.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run radar data publisher without ROS.")
    parser.add_argument('--cfg', help="Path to LUA configuration file for radar")
    parser.add_argument('--host_ip',        default='192.168.33.30', help='IP address of host.')
    parser.add_argument('--host_data_port', default=4098, type=int, help='Data port of host.')
    args = parser.parse_args()

    # Use a simple print function as default publisher for CLI runs
    radar = Radar(args, callback=print)


