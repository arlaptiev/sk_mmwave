import socket

# initialize phone socket
UDP_IP = "0.0.0.0"  # Listen on all interfaces
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening on UDP {UDP_PORT}...")

# initialize radar connection
def send_to_phone(message, phone_ip, phone_port):
    sock.sendto(message.encode(), (phone_ip, phone_port))
    print(f"Sent message to {phone_ip}:{phone_port}")

# if phone presses snap, then run radar file 
while True:
    data, addr = sock.recvfrom(1024)
    message = data.decode().strip()
    print(f"Received message from {addr}: {message}")
    if message == "RADAR STARTING DATA CAPTURE NOW":
        break


# collect data from radar


# process data from radar with fft


# find peaks with distances



# check if there is a strong peak at an inside box distance


# send boolean back to phone if box empty or not
phone_ip = "192.168.41.171"
phone_port = 6000
send_to_phone("TRUE", phone_ip, phone_port)
