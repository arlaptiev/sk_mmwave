# Signal Kinetics mmWave Kit

This repository contains the code for interfacing the TI's IWR1443 mmWave radar sensor in real-time, connected via Ethernet, as well as the iPhone sensor data, connected wirelessly.

### useful utilities:
- `python -m main` - starts the radar and phone nodes in continuous mode, prints the data to the console
- `python -m record` - starts the radar and phone nodes in continuous mode, saves the data to a data/recordings/[recording start time]/[node name]/[timestamp].pkl file
- `python -m live_fft` - plots the live FFT of the radar data, using matplotlib
- `python -m live_fft_cv` - plots the live FFT of the radar data, using OpenCV

## RADAR NODE

Initiates the node with the parameters inferred from the mmWave Studio lua file. Reads the raw IQ data stream from the data Ethernet socket continuously with `radar.run_polling([callback function])` or in a single read with `radar.read()`. For getting started with the IWR1443 radar and mmWave Studio, refer to docs/IWR1443_getting_started.md. Reference for the lua api: docs/Lua_API.md.

### How to run:
1. Open mmWaveStudio and run the configs/1443_mmwavestudio_config_continuous.lua file

2. Start the radar node:
```
python -m nodes.radar --cfg='configs/1443_mmwavestudio_config_continuous.lua'
```


### usage example: 
see notebooks/radar.ipynb

### common errors:
If radar data socket is already in use:
```bash
netstat -aon | findstr :4098
kill [task_number]
```

### notes:
- The messages from the radar node include timestamps but they are python-level timestamps, not the hardware-level timestamps of when the edge server received the data on the Ethernet cable. It is possible to get the hardware-level timestamps if implemented on a linux machine. 
- You can flush the radar data buffer by running: `radar.flush()`
- You can find the example of reading the mmWave Studio .bin recorded data file in notebooks/radar_bin_read.ipynb



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


### usage example: 
notebooks/phone.ipynb