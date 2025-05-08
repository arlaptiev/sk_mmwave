import os
import sys
import argparse
import csv
from datetime import datetime
import json
import numpy as np
import matplotlib.pyplot as plt
from numpy.fft import fft, fftfreq


# Add the project root and sibling directories to PYTHONPATH
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from nodes.radar import Radar

import cv2


def display_frame(message):
    frame = message.get("data", None)
    params = message.get("params", None)
    if frame is None or params is None:
        return

    # Radar parameters
    c = 3e8
    SAMPLES_PER_CHIRP = params['n_samples']
    SAMPLE_RATE = params['sample_rate']
    FREQ_SLOPE = params['chirp_slope']

    # Process RX0
    rx_idx = 0
    avg_chirps = np.mean(frame, axis=0)
    signal = avg_chirps[:, rx_idx]

    # FFT
    fft_result = fft(signal)
    fft_magnitude = np.abs(fft_result[:SAMPLES_PER_CHIRP // 2])
    fft_freqs = fftfreq(SAMPLES_PER_CHIRP, 1/SAMPLE_RATE)
    fft_meters = fft_freqs[:SAMPLES_PER_CHIRP // 2] * c / (2 * FREQ_SLOPE)

    # Only keep range 0–2 meters
    range_mask = (fft_meters >= 0.2) & (fft_meters <= 2.0)
    fft_magnitude = fft_magnitude[range_mask]
    fft_meters = fft_meters[range_mask]

    if fft_magnitude.size == 0:
        return  # avoid divide by zero or empty image

    # Normalize and visualize
    mag_norm = np.clip(fft_magnitude / np.max(fft_magnitude), 0, 1)
    img = (mag_norm * 255).astype(np.uint8)
    img = np.expand_dims(img, axis=0)
    img_color = cv2.applyColorMap(img, cv2.COLORMAP_INFERNO)
    img_color = cv2.resize(img_color, (1200, 800))

    cv2.imshow("Range FFT - RX0 (0-2m)", img_color)
    cv2.waitKey(1)



def main():
    parser = argparse.ArgumentParser(description="Start the mmWave Radar Node.")

    # radar args
    parser.add_argument("--cfg",            default='configs/1443_mmwavestudio_config_continuous.lua', type=str, help="Path to the Lua config file")
    parser.add_argument('--host_ip',        default='192.168.33.30', help='IP address of host.')
    parser.add_argument('--host_data_port', default=4098, type=int, help='Data port of host.')

    args = parser.parse_args()

    # Start the radar node
    radar = Radar(args)
    radar.run_polling(callback=display_frame)




if __name__ == "__main__":
    main()
