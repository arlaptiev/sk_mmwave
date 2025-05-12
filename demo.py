import socket
from types import SimpleNamespace
from nodes.radar import Radar

import numpy as np
import matplotlib.pyplot as plt

from scipy.fft import fft, fftfreq
from scipy.signal import windows
from scipy.fft import fftshift

from nodes.phone_node import Lidar
from src.lidar_dsp import detect_planes_and_box


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
lidar = Lidar()
img, depth_map, meta = lidar.read()
floor_dist, box_dist, table_dist = detect_planes_and_box(img, depth_map, meta)
print('Table distance', table_dist)


# ==== collect data from radar
frame = radar.read()
radar.close()
# avg over chirps
avg_chirps = np.mean(frame, axis=0)     # shape: (num_samples, num_rx)
# choose rx0
signal = avg_chirps                     # shape: (num_samples, num_rx)


# ==== process data from radar with fft
fft_result = fft(signal, axis=0)
rx = 0
fft_magnitude = np.abs(fft_result[:SAMPLES_PER_CHIRP // 2, rx])
fft_freqs = fftfreq(SAMPLES_PER_CHIRP, 1/SAMPLE_RATE)
fft_meters = fft_freqs[:SAMPLES_PER_CHIRP // 2] * c / (2 * FREQ_SLOPE)

# ==== find low and high bounds from lidar data
low_bound = table_dist
high_bound = table_dist + .35


# ==== find peaks with distances
range_mask = (fft_meters >= low_bound) & (fft_meters <= high_bound)
fft_magnitude_masked = fft_magnitude[range_mask]
fft_meters_masked = fft_meters[range_mask]


# ==== check if there is a strong peak at an inside box distance
THRESHOLD = 450000
detection = (fft_magnitude_masked > THRESHOLD).any()
masked_max = np.max(fft_magnitude_masked)
print('Max within range:', masked_max)


# ==== send boolean back to phone if box empty or not
message = "TRUE" if detection else "FALSE"
print("Detection", detection)

def send_to_phone(message, ip, port):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.sendto(message.encode(), (ip, port))
  sock.close()

ip = "192.168.41.62"
port = 9999
send_to_phone(message, ip, port)

plt.figure(figsize=(12, 9))
plt.plot(fft_meters,  np.abs(fft_result[:SAMPLES_PER_CHIRP // 2, 0]), color='blue', label='RX1', alpha=0.7)
plt.plot(fft_meters,  np.abs(fft_result[:SAMPLES_PER_CHIRP // 2, 1]), color='orange', label='RX2', alpha=0.7)
plt.plot(fft_meters,  np.abs(fft_result[:SAMPLES_PER_CHIRP // 2, 2]), color='green', label='RX3', alpha=0.7)
plt.plot(fft_meters,  np.abs(fft_result[:SAMPLES_PER_CHIRP // 2, 3]), color='red', label='RX4', alpha=0.7)
plt.vlines([low_bound, high_bound], [0, 0], [masked_max + 1000, masked_max + 1000])
plt.title('Frequency Domain Signals')
plt.xlabel('Distance (m)')
plt.ylabel('Magnitude')
plt.legend()
plt.xlim(0,1.5)

# plt.show()



