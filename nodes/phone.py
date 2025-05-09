#!/usr/bin/env python3

"""TCP server to receive JSON payloads from phone and save image, depth, and metadata."""

import os
import json
import base64
import socket
import argparse
from datetime import datetime
import io
import numpy as np


class Lidar:
    def __init__(self, host='0.0.0.0', port=5005):
        """Initializes the TCP server to listen for incoming lidar data."""
        self.host = host
        self.port = port
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        os.makedirs('captures', exist_ok=True)

    def run_polling(self, callback=None):
        """Begins listening for incoming connections and handles them."""
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen()
        print(f"[INFO] Listening on TCP {self.host}:{self.port}...")

        while True:
            conn, addr = self.server_sock.accept()
            print(f"[INFO] Connected by {addr}")
            try:
                with conn.makefile('rb') as f:
                    print(f"[INFO] Waiting to receive data from {addr}")
                    line = f.readline()

                if not line:
                    print(f"[WARN] No data received from {addr}")
                    continue

                try:
                    frame = json.loads(line.decode('utf-8'))
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Invalid JSON: {e}")
                    continue

                now = datetime.now()

                img_bytes = base64.b64decode(frame['image'])
                depth_bytes = base64.b64decode(frame['depth'])
                meta = frame.get('meta', {})

                W, H = 256, 192
                depth_map = np.load(io.BytesIO(depth_bytes))
                depth_map = depth_map.reshape((H, W))

                # radar_msg = {'data': frame_data, 'node': 'radar', 'timestamp': timestamp, 'params': self.params}
                lidar_msg = {'data': {'img_bytes': img_bytes, 'depth_map': depth_map}, 'node': 'lidar', 'timestamp': now, 'meta': meta}

                if callback:
                    callback(lidar_msg)

            except Exception as e:
                self.server_sock.close()
                print(f"[ERROR] Error handling connection: {e}")
            finally:
                conn.close()

    def read(self):
        """Reads a single JSON-encoded frame from the next incoming connection.

        Returns:
            tuple: (img_bytes, depth_bytes, meta) if successful, else None
        """
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen()
        print(f"[INFO] Waiting for a single connection on {self.host}:{self.port}...")

        conn, addr = self.server_sock.accept()
        print(f"[INFO] Connected by {addr}")
        try:
            with conn.makefile('rb') as f:
                line = f.readline()

            if not line:
                print(f"[WARN] No data received from {addr}")
                return None

            try:
                frame = json.loads(line.decode('utf-8'))
            except json.JSONDecodeError as e:
                print(f"[ERROR] Invalid JSON: {e}")
                return None

            img_bytes = base64.b64decode(frame['image'])
            depth_bytes = base64.b64decode(frame['depth'])
            meta = frame.get('meta', {})

            return img_bytes, depth_bytes, meta

        except Exception as e:
            print(f"[ERROR] Error during read: {e}")
            return None
        finally:
            conn.close()
            self.close()

        

    def close(self):
        self.server_sock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="TCP server to receive and store phone image/depth frames.")
    parser.add_argument('--host', default='0.0.0.0', help="Host IP to bind to.")
    parser.add_argument('--port', default=5005, type=int, help="TCP port to listen on.")
    args = parser.parse_args()

    server = Lidar(host=args.host, port=args.port)
    try:
        server.listen()
    except KeyboardInterrupt:
        print("[INFO] Shutting down server.")
    finally:
        server.close()
