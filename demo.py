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

import time


while True:

  start_time = time.time()

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


  radar_init_time = time.time()

  print("[TIME] Radar took", radar_init_time - start_time, "seconds to init")

  # ==== initialize phone socket
  lidar = Lidar()
  img, depth_map, meta = lidar.read()

  
  phone_lidar_read_time = time.time()

  print("[TIME] Lidar sending took", phone_lidar_read_time - radar_init_time, "seconds")


  floor_dist, box_dist, table_dist = detect_planes_and_box(img, depth_map, meta)
  print('Table distance', table_dist)

  lidar_detect_time = time.time()

  print("[TIME] Lidar detecting took", lidar_detect_time - phone_lidar_read_time, "seconds")



  # ==== collect data from radar
  frame = radar.read()
  radar.close()
  # avg over chirps
  avg_chirps = np.mean(frame, axis=0)     # shape: (num_samples, num_rx)
  # choose rx0
  signal = avg_chirps                     # shape: (num_samples, num_rx)

  radar_data_time = time.time()

  print("[TIME] Radar data reading took", radar_data_time - lidar_detect_time, "seconds")


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

  radar_processing_time = time.time()

  print("[TIME] Radar fft processing took", radar_processing_time - radar_data_time, "seconds")


  def send_to_phone(message, ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode(), (ip, port))
    sock.close()

  ip = "192.168.41.62"
  port = 9999
  send_to_phone(message, ip, port)

  udp_sendphone_time = time.time()

  print("[TIME] UDP send to phone time took", udp_sendphone_time - radar_processing_time, "seconds")

  print("[TIME] TOTAL TIME:", time.time() - start_time, "seconds")






