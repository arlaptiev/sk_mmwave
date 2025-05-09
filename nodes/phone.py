import socket
import json
import base64
import os
from datetime import datetime


def listen_to_phone():
    HOST = '0.0.0.0'
    PORT = 5005

    # Ensure captures directory exists
    os.makedirs('captures', exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((HOST, PORT))
        server_sock.listen()
        print(f'Listening on TCP {HOST}:{PORT}…')

        while True:
            conn, addr = server_sock.accept()
            print(f'Connected by {addr}')
            try:
                # Read one full JSON line (blocking) from the client
                with conn.makefile('rb') as f:
                    print(f"[Server] Waiting to receive data from {addr}")
                    line = f.readline()

                if not line:
                    print("⚠️  No data received from", addr)
                    continue

                # Parse JSON
                try:
                    frame = json.loads(line.decode('utf-8'))
                except json.JSONDecodeError as e:
                    print("❌ Invalid JSON:", e)
                    continue

                # Use server's current date/time for human-readable folder - might need to change it later to align with timestamps from radar
                now = datetime.now()
                readable_ts = now.strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]

                # Create output directory
                out_dir = os.path.join('captures', readable_ts)
                os.makedirs(out_dir, exist_ok=True)

                # Decode and save payloads
                img_bytes   = base64.b64decode(frame['image'])
                depth_bytes = base64.b64decode(frame['depth'])
                meta        = frame.get('meta', {})

                with open(os.path.join(out_dir, 'frame.jpg'), 'wb') as img_f:
                    img_f.write(img_bytes)
                with open(os.path.join(out_dir, 'depth.bin'), 'wb') as depth_f:
                    depth_f.write(depth_bytes)
                with open(os.path.join(out_dir, 'meta.json'), 'w') as meta_f:
                    json.dump(meta, meta_f, indent=2)

                print(f'✅ Saved capture {readable_ts} → {out_dir}')

            except Exception as e:
                print("Error handling connection:", e)
            finally:
                conn.close()


if __name__ == '__main__':
    listen_to_phone()
