

Starting radar node:
cd sk_mmwave
python -m nodes.radar configs\1443_mmwavestudio_config.lua


If radar data socket is already in use:
netstat -aon | findstr :4098
kill [task_number]


# How to run the phone node:

1. Get the edge server wireless ip address:
ipconfig
On mac: ipconfig getifaddr en0

2. Disable the firewall on the edge server:
On mac: network -> firewall -> turn off firewall

3. Set the host ip address in the phone app settings

4. Run the phone node:
python -m nodes.phone