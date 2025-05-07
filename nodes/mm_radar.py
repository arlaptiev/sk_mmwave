import mmwave as mm
from mmwave.dataloader import DCA1000
import socket

dca = DCA1000()

# dca.data_socket.setblocking(True)
# dca.data_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131071*5)

print('Reading')

adc_data = dca.read(5)

print('adc data', adc_data)

dca.close()