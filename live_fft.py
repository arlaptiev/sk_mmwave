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




# Global variables for plot handles (to update instead of redrawing)
fig, (ax_time, ax_freq) = plt.subplots(2, 1, figsize=(12, 9))
line_time, = ax_time.plot([], [])
line_freq, = ax_freq.plot([], [])

plt.ion()  # Enable interactive mode
plt.show()


def display_frame(message):
    frame = message.get("data", None)
    params = message.get("params", None)

    # Radar parameters
    c = 3e8
    SAMPLES_PER_CHIRP = params['n_samples']
    SAMPLE_RATE = params['sample_rate']
    FREQ_SLOPE = params['chirp_slope']

    # Processing
    avg_chirps = np.mean(frame, axis=0)  # shape: (n_samples, n_rx)
    signal = avg_chirps

    fft_result = fft(signal, axis=0)
    fft_freqs = fftfreq(SAMPLES_PER_CHIRP, 1/SAMPLE_RATE)
    fft_meters = fft_freqs * c / (2 * FREQ_SLOPE)
    half_range = SAMPLES_PER_CHIRP // 2


    # Clear and replot
    ax_time.cla()
    ax_freq.cla()

    colors = ['blue', 'orange', 'green', 'red']
    labels = ['RX1', 'RX2', 'RX3', 'RX4']

    # Time Domain Plot
    for rx in range(signal.shape[1]):
        ax_time.plot(signal[:, rx], color=colors[rx], label=labels[rx], alpha=0.7)
    ax_time.set_title('Time Domain Signals')
    ax_time.set_xlabel('Sample Index')
    ax_time.set_ylabel('Amplitude')
    ax_time.legend()
    ax_time.set_xlim(0, SAMPLES_PER_CHIRP)

    # Frequency Domain Plot
    for rx in range(signal.shape[1]):
        ax_freq.plot(fft_meters[:half_range], np.abs(fft_result[:half_range, rx]), color=colors[rx], label=labels[rx], alpha=0.7)
    ax_freq.set_title('Frequency Domain Signals')
    ax_freq.set_xlabel('Distance (m)')
    ax_freq.set_ylabel('Magnitude')
    ax_freq.legend()
    ax_freq.set_xlim(0, 1.5)
    # ax_freq.set_ylim(0, np.max(np.abs(fft_result[:half_range])) * 1.1)

    plt.tight_layout()
    plt.pause(0.001)






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
