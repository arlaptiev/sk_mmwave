import argparse
from src.radar import Radar
import cv2
import numpy as np

n_receivers = 4
samples_per_chirp = 128
n_chirps_per_frame = 128
n_tdm = 1


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


def reshape_frame(msg, n_chirps_per_frame, samples_per_chirp, n_receivers):
    data = np.array(msg['data'], dtype=np.int16)

    data = data.reshape(-1, 8)  # Assuming we have 4 antennas

    data = data[:, :4] + 1j * data[:, 4:]

    data = data.reshape(n_chirps_per_frame, samples_per_chirp, n_receivers)

    # deinterleve if theres TDM
    if n_tdm > 1:  # TODO: Pretty sure we're not using TDM
        data_i = [data[i::n_tdm, :, :] for i in range(n_tdm)]
        data = np.concatenate(data_i, axis=-1)

    return data

prev_frame = None

def update_frame(data):
    global prev_frame
    reshaped_frame = reshape_frame(
        data, n_chirps_per_frame, samples_per_chirp, n_receivers
    )

    raw_frame = reshaped_frame

    reshaped_frame = reshaped_frame if prev_frame is None else reshaped_frame - prev_frame

    prev_frame = raw_frame

    # Process the data
    fft_data = fft_processs(reshaped_frame)

    # Normalize and color the data
    img = normalize_and_color(fft_data, max_val=0, cmap=cv2.COLORMAP_JET)

    img = cv2.resize(img, (800, 600))

    # Display the image
    cv2.imshow("FFT Data", img)
    cv2.waitKey(1)  # Allow OpenCV to process the window events


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record data from the DCA1000")
    parser.add_argument("--cfg", type=str, required=True, help="Path to the .lua file")

    args = parser.parse_args()

    # Initialize the radar
    radar = Radar(args.cfg, cb=update_frame)