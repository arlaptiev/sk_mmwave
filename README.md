

Starting radar node:
cd sk_mmwave
python -m nodes.radar configs\1443_mmwavestudio_config.lua

If radar data socket is already in use:
netstat -aon | findstr :4098
kill [task_number]