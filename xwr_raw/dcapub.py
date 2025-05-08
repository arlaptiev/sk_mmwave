#!/usr/bin/env/python3

"""Radar data publisher.

Publisher requires a dedicated thread to receive UDP frames.

Modified from: https://github.com/ConnectedSystemsLab/xwr_raw_ros/blob/main/src/xwr_raw/radar_pub.py
"""

import socket
from typing import List

from xwr_raw.radar_config import RadarConfig
from xwr_raw.dca1000 import DCA1000
from xwr_raw.frame_buffer import FrameBuffer


class DCAPub:

    def __init__(
        self,
        cfg: str,
        dca_ip: str = "192.168.33.181",
        host_ip: str = "192.168.33.30",
        host_data_port: int = 4098,
    ):
        """
        Recevies UDP frames from DCA1000 and publishes them to a socket.

        Note: In ConnectedSystems they use the demo application and the .cfg file generated from the online tool.
        Since we're using the LUA scripts, we don't need to do the configuration steps

        Future work: Look at also using the demo application. May be possible to make this cross platform

        Args:
            cfg (str): Path to the .lua file used in mmWaveStudio to configure the radar
            dca_ip (str): IP address of the DCA1000
            host_ip (str): IP address of the host
            host_data_port (int): Data port of the host
        """

        self.config = RadarConfig(cfg)
        self.params = self.config.get_params()

        self.dca1000 = DCA1000(dca_ip=None,
                               dca_cmd_port=None,
                               host_ip=host_ip,
                               host_cmd_port=None,
                               host_data_port=host_data_port)
        self.dca1000.capturing = True

        if hasattr(self.dca1000, "data_socket"):
            self.dca1000.data_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_RCVBUF, 131071 * 5
            )
        
        self.frame_buffer = FrameBuffer(
            2 * self.params["frame_size"], self.params["frame_size"]
        )

    def update_frame_buffer(self):
        seqn, bytec, msg = self.dca1000.recv_data()
        frame_data, new_frame = self.frame_buffer.add_msg(seqn, msg)
        return frame_data, new_frame
    
    def close(self):
        self.dca1000.close()