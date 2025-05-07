import argparse
import cv2
import numpy as np
from src.xwr.radar_config import RadarConfig
from src.dsp import reshape_frame
import pandas as pd
import json


def random_noise_elimination(frame, freq, chirp_sample_rate):
    """
    Remove the random noise from the data.

    From HomeOSD: The random noise can be removed by using the moving average of a window with the length of the period
    of frequency / 2.

    Args:
        frame (np.ndarray): The input fft array (n_chirps_per_frame, samples_per_chirp, n_receivers).
        freq (float): The frequency we're interested in.
        chirp_sample_rate (float): The chirp sample rate in Hz.
    """
    # Window should be number of sampling points associated with (period of frequency) / 2
    period = 1 / freq

    # window_size = int(chirp_sample_rate * period / 2)
    window_size = int(chirp_sample_rate * period / 2)

    # Create a moving average filter
    kernel = np.ones(window_size) / window_size

    # Apply separately to real and imaginary parts
    real_filtered = np.apply_along_axis(
        lambda m: np.convolve(m.real, kernel, mode="same"), axis=0, arr=frame
    )
    imag_filtered = np.apply_along_axis(
        lambda m: np.convolve(m.imag, kernel, mode="same"), axis=0, arr=frame
    )

    # pad = window_size // 2
    # trimmed = real_filtered[pad:-pad] + 1j * imag_filtered[pad:-pad]

    return real_filtered + 1j * imag_filtered


def normalize_and_color(data, max_val=0, cmap=None):
    if max_val <= 0:
        max_val = np.max(data)

    img = (data / max_val * 255).astype(np.uint8)
    if cmap:
        img = cv2.applyColorMap(img, cmap)
    return img


def fft_processs(adc_samples):
    fft_range = np.fft.fft(adc_samples, axis=1)
    fft_range_doppler = np.fft.fft(fft_range, axis=0)
    fft_range_azi = np.fft.fft(fft_range_doppler, axis=2)

    # fft_mag = np.log(np.abs(fft_range_azi_cd))
    # return fft_range_azi
    # fft_range_azi_cd = np.sum(fft_range_azi, 0)

    fft_mag = np.fft.fftshift(np.log(np.abs(fft_range_doppler[:, :, 0])), axes=0)
    return fft_mag


prev_frame = None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record data from the DCA1000")
    parser.add_argument("--data", type=str, required=True, help="Path to the .csv file")
    parser.add_argument("--cfg", type=str, required=True, help="Path to the .lua file")

    args = parser.parse_args()

    # Initalize the radar config
    config = RadarConfig(args.cfg).get_params()

    n_chirps_per_frame = config["n_chirps"]
    n_receivers = config["n_rx"]
    samples_per_chirp = config["n_samples"]

    # Read in the frames
    df = pd.read_csv(args.data, chunksize=1)

    for chunk in df:
        data_json = json.loads(chunk["data"].iloc[0])

        data = np.array(data_json, dtype=np.int16)

        # Reshape the data into a 3D array (n_chirps_per_frame, samples_per_chirp, n_receivers) of IQ samples
        reshaped_frame = reshape_frame(
            data,
            n_chirps_per_frame,
            samples_per_chirp,
            n_receivers,
        )

        processed_frame = (
            reshaped_frame if prev_frame is None else reshaped_frame - prev_frame
        )

        processed_frame = random_noise_elimination(
            processed_frame, freq=40, chirp_sample_rate=config["chirp_sampling_rate"]
        )

        fft_data = fft_processs(processed_frame)

        # Normalize and color the data
        img = normalize_and_color(fft_data, max_val=0, cmap=cv2.COLORMAP_JET)

        img = cv2.resize(img, (800, 600))

        # Display the image
        cv2.imshow("FFT Data", img)
        cv2.waitKey(1)  # Allow OpenCV to process the window events