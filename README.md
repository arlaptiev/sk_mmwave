# Signal Kinetics mmWave Kit

This repository contains the code for interfacing the TI's IWR1443 mmWave radar sensor in real-time, connected via Ethernet, as well as the iPhone sensor data (camera + lidar + position), connected wirelessly.

### Useful utilities:
- `python -m main` - starts the radar and phone nodes in continuous mode, prints the data to the console
- `python -m record` - starts the radar and phone nodes in continuous mode, saves the data to a data/recordings/[recording start time]/[node name]/[timestamp].pkl file
- `python -m live_fft` - plots the live FFT of the radar data, using matplotlib
- `python -m live_fft_cv` - plots the live FFT of the radar data, using OpenCV

### Object Detection Demo:

- `python -m object_detection_demo` - demo script running the radar node and the phone node, detecting presence of an object inside a box on the table.

## RADAR NODE

Initiates the node with the parameters inferred from the mmWave Studio lua file. Reads the raw IQ data stream from the data Ethernet socket continuously with `radar.run_polling([callback function])` or in a single read with `radar.read()`. For getting started with the IWR1443 radar and mmWave Studio, refer to [docs/IWR1443_getting_started.md](docs/IWR1443_getting_started.md). Reference for the lua api: [docs/Lua_API.md](docs/Lua_API.md).

### How to run:
1. Open mmWaveStudio and run the configs/1443_mmwavestudio_config_continuous.lua file (IWR1443 should start flashing green)

2. Start the radar node:
```
python -m nodes.radar --cfg='configs/1443_mmwavestudio_config_continuous.lua'
```


### Usage & outputs example: 
see [notebooks/radar.ipynb](notebooks/radar.ipynb)

### Common errors:
If radar data socket is already in use, kill the process that is using it:
```bash
netstat -aon | findstr :4098
kill [task_number]
```

If the data stops flowing, and the IWR1443 stops flashing green, it is most likely that the data socket buffer is full. You have to rerun the lua script in mmWave Studio to reset the data stream. You can avoid this by setting the radar parameters such that less data is sent (or less frequently), you can also set `radar.run_polling(lose_frames=True)` if you don't care about collecting consecutive frames (again, this will drop some data!). To flush the data socket buffer, run `radar.flush()`.

### Notes:
- The messages from the radar node include timestamps but they are python-level timestamps, not the hardware-level timestamps of when the edge server received the data on the Ethernet cable. It is possible to get the hardware-level timestamps if implemented on a linux machine.
- You can find the useful example of reading the mmWave Studio .bin recorded data file in [notebooks/radar_bin_read.ipynb](notebooks/radar_bin_read.ipynb). This is useful for debugging and testing the radar node against the data recorded in mmWave Studio.



## PHONE NODE

### How to run:
1. Get the edge server wireless ip address:
```bash
ipconfig
```
On mac: 
```bash
ipconfig getifaddr en0
```

2. Disable the firewall on the edge server:
On mac: network -> firewall -> turn off firewall

3. Set the host ip address in the phone app settings

4. Run the phone node:
```bash
python -m nodes.phone
```


### Usage & outputs example: 
see [notebooks/phone.ipynb](notebooks/phone.ipynb)