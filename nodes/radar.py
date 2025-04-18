#!/usr/bin/env python3

"""Simple publisher of raw radar data, without ROS dependency."""

import os
import sys
import time
import argparse
import numpy as np

from xwr_raw.radar_lua_config import LuaRadarConfig
from xwr_raw.dca_data_pub import DCADataPub


def init_radar_node(args, publisher=None, verbose=False):
    """Initializes radar capture and starts publishing frames.

    Args:
        args: Parsed arguments with:
            `lua`           - Path to LUA configuration file for radar
            `host_ip`       - IP address of host
            `host_port`     - Data port of host
        publisher (callable, optional): Function to handle published radar data.
        verbose (bool): If True, prints status messages.
    """
    lua_path = os.path.abspath(args.lua)
    if not os.path.isfile(lua_path):
        raise FileNotFoundError(f"LUA config file not found: {lua_path}")

    if verbose:
        print(f"[INFO] Reading LUA config from: {lua_path}")

    with open(lua_path, 'r') as f:
        lua = f.readlines()

    if verbose:
        print(f"[INFO] Connecting radar with host {args.host_ip}:{args.host_data_port}")

    radar = DCADataPub(
        lua,
        host_ip=args.host_ip,
        host_data_port=int(args.host_data_port)
    )

    if verbose:
        print("[INFO] Radar connected. Starting data capture...")

    try:
        while True:
            frame_data, new_frame = radar.update_frame_buffer()
            if new_frame:
                radar_msg = {'data': frame_data}

                if verbose:
                    print(f"[DEBUG] New frame received. Length: {len(frame_data)}")

                if publisher:
                    publisher(radar_msg)

            time.sleep(0.01)  # Prevents busy-looping
    except KeyboardInterrupt:
        if verbose:
            print("[INFO] Stopping radar capture.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run radar data publisher without ROS.")
    parser.add_argument('lua', help="Path to LUA configuration file for radar")
    parser.add_argument('--host_ip',        default='192.168.33.30', help='IP address of host.')
    parser.add_argument('--host_data_port', default=4098, type=int, help='Data port of host.')
    parser.add_argument('--verbose', action='store_true', help='Print detailed debug info')
    args = parser.parse_args()

    # Use a simple print function as default publisher for CLI runs
    init_radar_node(args, publisher=print, verbose=args.verbose)

