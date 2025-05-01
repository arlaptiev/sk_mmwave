import socket

def listen_to_phone():
    UDP_IP = "0.0.0.0"  # Listen on all interfaces
    UDP_PORT = 5005

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"Listening on UDP {UDP_PORT}...")

    while True:
        data, addr = sock.recvfrom(1024)
        print(f"Received message from {addr}: {data.decode()}")

