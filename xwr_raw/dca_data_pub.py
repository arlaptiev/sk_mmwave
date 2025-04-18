"""Radar data publisher.

Publisher requires a dedicated thread to receive UDP frames.
"""

import time
import socket
from typing import List

from xwr_raw.radar_lua_config import LuaRadarConfig
from xwr_raw.dca1000 import DCA1000
from xwr_raw.frame_buffer import FrameBuffer


class DCADataPub():
    """Same as DCAPub but without configuration and control over DCA1000.
    """
    def __init__(self,
                 lua            : List[str],
                 host_ip        : str = '192.168.33.30',
                 host_data_port : int = 5098):

        self.config = LuaRadarConfig(lua)
        self.params = self.config.get_params()
        self.dca1000 = DCA1000(dca_ip=None,
                               dca_cmd_port=None,
                               host_ip=host_ip,
                               host_cmd_port=None,
                               host_data_port=host_data_port)
        self.dca1000.capturing = True

        if hasattr(self.dca1000, 'data_socket'):
            self.dca1000.data_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131071*5)
        self.frame_buffer = FrameBuffer(2*self.params['frame_size'], self.params['frame_size'])


    def update_frame_buffer(self):
        seqn, bytec, msg = self.dca1000.recv_data()
        frame_data, new_frame = self.frame_buffer.add_msg(seqn, msg)
        return frame_data, new_frame