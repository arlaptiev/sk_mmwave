import socket
from types import SimpleNamespace
from nodes.radar import Radar

import numpy as np
import matplotlib.pyplot as plt

from scipy.fft import fft, fftfreq
from scipy.signal import windows
from scipy.fft import fftshift

# ==== initialize radar and set params
args = SimpleNamespace(**{
  'cfg': 'configs/1443_mmwavestudio_config_continuous.lua',
  'host_ip': '192.168.33.30',
  'host_data_port': 4098,
})
radar = Radar(args)

c = 3e8                                                 # speed of light - m/s
SAMPLES_PER_CHIRP = radar.params['n_samples']           # adc number of samples per chirp
SAMPLE_RATE = radar.params['sample_rate']               # digout sample rate in Hz
FREQ_SLOPE = radar.params['chirp_slope']                # frequency slope in Hz (/s)



# ==== initialize phone socket
UDP_IP = "0.0.0.0"  # Listen on all interfaces
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening on UDP {UDP_PORT}...")

addr = ""

# if phone presses snap, then run radar file 
while True:
    data, addr = sock.recvfrom(1024)
    message = data.decode().strip()
    print(f"Received message from {addr}: {message}")
    if message == "RADAR STARTING DATA CAPTURE NOW":
        break
    

def send_to_phone(message, addr):
    sock.sendto(message.encode(), addr)
    print(f"Sent message to {phone_ip}:{phone_port}")




# ==== collect data from radar
frame = radar.read()
# avg over chirps
avg_chirps = np.mean(frame, axis=0)     # shape: (num_samples, num_rx)
# choose rx0
signal = avg_chirps[:, 0]               # shape: (num_samples,)


# ==== process data from radar with fft
fft_result = fft(signal)
fft_magnitude = np.abs(fft_result[:SAMPLES_PER_CHIRP // 2])
fft_freqs = fftfreq(SAMPLES_PER_CHIRP, 1/SAMPLE_RATE)
fft_meters = fft_freqs[:SAMPLES_PER_CHIRP // 2] * c / (2 * FREQ_SLOPE)

# ==== find low and high bounds from lidar data
low_bound = 0.5
high_bound = 5

# ==== find peaks with distances
range_mask = (fft_meters >= low_bound) & (fft_meters <= high_bound)
fft_magnitude = fft_magnitude[range_mask]
fft_meters = fft_meters[range_mask]


# ==== check if there is a strong peak at an inside box distance
THRESHOLD = 450000
detection = any(fft_magnitude > THRESHOLD)


# ==== send boolean back to phone if box empty or not
phone_ip = "192.168.41.215"
phone_port = 6000
if detection:
  send_to_phone("TRUE", addr)
else:
  send_to_phone("FALSE", addr)
