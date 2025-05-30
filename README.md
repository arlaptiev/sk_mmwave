# Signal Kinetics mmWave Kit

## RADAR NODE:

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



## PHONE NODE:

### How to run:
1. Get the edge server wireless ip address:
ipconfig
On mac: ipconfig getifaddr en0

2. Disable the firewall on the edge server:
On mac: network -> firewall -> turn off firewall

3. Set the host ip address in the phone app settings

4. Run the phone node:
```bash
python -m nodes.phone
```


### usage example: 
notebooks/phone.ipynb