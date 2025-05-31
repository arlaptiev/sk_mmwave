#!/usr/bin/env python3

"""TCP server to receive JSON payloads from phone and save image, depth, and metadata."""

import os
import json
import base64
import socket
import argparse
from datetime import datetime
import numpy as np
import cv2


class Phone:
    def __init__(self, host='0.0.0.0', port=5005):
        """Initializes the TCP server to listen for incoming phone data."""
        self.host = host
        self.port = port
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.prev_addr = ""

    def run_polling(self, callback=None):
        """Begins listening for incoming connections and handles them."""
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen()
        print(f"[INFO] Listening on TCP {self.host}:{self.port}...")

        while True:
            conn, addr = self.server_sock.accept()
            self.prev_addr = addr
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

                # bytes to depth map
                W, H = 256, 192
                depth_array = np.frombuffer(depth_bytes, dtype=np.float32)
                depth_map = depth_array.reshape((H, W))

                # bytes to img
                img_array = np.frombuffer(img_bytes, dtype=np.uint8)
                cv2_image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

                phone_msg = {'data': {'img': cv2_image, 'depth_map': depth_map, 'meta': meta}, 'node': 'phone', 'timestamp': now}

                if callback:
                    callback(phone_msg)

            except Exception as e:
                self.server_sock.close()
                print(f"[ERROR] Error handling connection: {e}")
            finally:
                conn.close()

    def read(self):
        """Reads a single JSON-encoded frame from the next incoming connection.

        Returns:
            tuple: (img, depth_map, meta) if successful, else None
        """
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen()
        print(f"[INFO] Waiting for a single connection on {self.host}:{self.port}...")

        conn, addr = self.server_sock.accept()
        self.prev_addr = addr
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

            # bytes to depth map
            W, H = 256, 192
            depth_array = np.frombuffer(depth_bytes, dtype=np.float32)
            depth_map = depth_array.reshape((H, W))

            # bytes to img
            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            cv2_image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            return cv2_image, depth_map, meta

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

    phone = Phone(host=args.host, port=args.port)
    try:
        phone.run_polling(callback=print)
    except KeyboardInterrupt:
        print("[INFO] Shutting down server.")
    finally:
        phone.close()
