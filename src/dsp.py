def reshape_frame(data, n_chirps_per_frame, samples_per_chirp, n_receivers):
    """
    Reshape the raw data into a 3D array of shape (n_chirps_per_frame, samples_per_chirp, n_receivers).
    """
    data = data.reshape(-1, 8)  # Assuming we have 4 antennas

    data = data[:, :4] + 1j * data[:, 4:]

    data = data.reshape(n_chirps_per_frame, samples_per_chirp, n_receivers)

    # # deinterleve if theres TDM
    # if n_tdm > 1:  # TODO: Pretty sure we're not using TDM
    #     data_i = [data[i::n_tdm, :, :] for i in range(n_tdm)]
    #     data = np.concatenate(data_i, axis=-1)

    return data