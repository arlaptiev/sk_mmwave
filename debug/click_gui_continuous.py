import pyautogui
import time
import subprocess

import socket
import os

# import sys
# sys.path.append('..')
# import optitrack_streaming

def update_cfg_timestamp():
    # Code based on: https://stackoverflow.com/questions/4719438/editing-specific-line-in-text-file-in-python
    timestamp = int(time.time()*100)
    with open('cf.json', 'r') as f:
        data = f.readlines()

    data[22] = f'      "filePrefix": "adc_data_{timestamp}",\n'
    with open('cf.json', 'w') as f:
        f.writelines( data )
    return timestamp

def run_powershell(cmd):
    completed = subprocess.run(["powershell", "-Command", cmd], capture_output=True, cwd="C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc")
    return completed

def run_powershell_nonblocking(cmd):
    completed = subprocess.Popen(["powershell", "-Command", cmd], cwd="C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc")
    return completed

def get_latest_binary(folder):
    filenames = sorted(os.listdir(folder))
    # print(filenames)
    for k, filename in enumerate(filenames[::-1]):
        if filename[-4:] != '.bin': continue
        return int(filename[8:18])

def get_created_modified_date(folder, timestamp):
    filename = f'{folder}\\adc_data_{timestamp}_Raw_0.bin'
    print(os.path.getmtime(filename))
    print(os.path.getctime(filename))
    return os.path.getctime(filename), os.path.getmtime(filename)

if __name__=='__main__':
    data_folder = 'C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc\\Data'
    current_ts = None
    use_robot_comp = True
    use_optitrack = False

    cwd = os.getcwd()
    print(cwd)
    resp = run_powershell(f"C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc\\DCA1000EVM_CLI_Control.exe fpga {cwd}\\cf.json")
    # print(resp.returncode)
    print(resp.stdout.decode("utf-8"))
    resp = run_powershell(f"C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc\\DCA1000EVM_CLI_Control.exe record {cwd}\\cf.json")
    # print(resp.returncode)
    print(resp.stdout.decode("utf-8"))

    
    # resp = run_powershell("C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc\\DCA1000EVM_CLI_Control.exe start_record cf.json")

    opt_ip = 'localhost'
    opt_port = 6000
    if use_optitrack: 
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((opt_ip,opt_port))
        server_socket.listen()
        (clientConnected, clientAddress) = server_socket.accept()
        print("Accepted a connection request from %s:%s"%(clientAddress[0], clientAddress[1]))


    ip = '192.168.41.146' # IP address of other computer
    port = 8080
    if use_robot_comp:
        clientSocket = socket.socket()
        clientSocket.bind(('192.168.33.30',8077))
        clientSocket.connect((ip,port))
    print ("connected to the server!")
    i = 0
    while(True):
        print(f'About to recieve')
        if use_robot_comp:
            dataFromServer = clientSocket.recv(64)
            rx_timestamp = time.time()
        else:
            dataFromServer = b'M'
            # time.sleep(0.3)
            # time.sleep(2)
        print(f'Recieved {dataFromServer}')

        data = "Invalid Cmd"
        if dataFromServer == b'R':
            # reset setting
            data = "done"
            print(f'resetting')

        if dataFromServer == b'M':
            # time.sleep(1/8)
            # Take a new measurement 
            print(f'Taking measurement {i}')
            i += 1
            timestamp = update_cfg_timestamp()
            resp = run_powershell(f"C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc\\DCA1000EVM_CLI_Control.exe stop_record {cwd}\\cf.json")
            # print("1: ", resp)
            resp = run_powershell_nonblocking(f"C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc\\DCA1000EVM_CLI_Record.exe start_record {cwd}\\cf.json")
            # print("2: ", resp)
            time.sleep(0.5/2)

            pyautogui.click(40, 825) # Original, Working after adding optitrack
            # pyautogui.click(30, 940) # New resolution after member event
            # pyautogui.click(30, 700) # New resolution after member event

            # time.sleep(70/8*2+3) # CIRCLE TODO: This sleep needs to be long enough for radar to finish, depends on radar settings
            #time.sleep(70/8+3) # TODO: This sleep needs to be long enough for radar to finish, depends on radar settings
            time.sleep(70/8+3+2) # Tara changing delay to see if it fixes the file sizes after windows update oct 11
            try:
                ctime, mtime = get_created_modified_date(data_folder, timestamp)
            except: # TODO: this is hacky
                try:
                    time.sleep(10)
                    ctime, mtime = get_created_modified_date(data_folder, timestamp)
                except:
                    ctime = -1
                    mtime = -1
                    print(f'This measurement failed!!')
            
            data = f'{timestamp},{ctime},{mtime}'
            print(f'Sending {data}')        
            if use_robot_comp: 
                clientSocket.send(data.encode())
            else:
                # input()
                pass
                print(f'Delta: {(mtime-ctime)}') 

        # else:
        #     # TMP for testing sync
        #     print(dataFromServer)
        #     print(float(dataFromServer.decode()))
        #     timestamp = float(dataFromServer.decode())
        #     print(f'Received timestamp: {rx_timestamp}')
        #     print(f'Delta: {timestamp - rx_timestamp}')
        #     timestamp = rx_timestamp
        #     ctime=0
        #     mtime=0

        if dataFromServer == b'start_ant':
            if use_optitrack:
                clientConnected.send("start_ant".encode())
        if dataFromServer == b'stop_ant':
            if use_optitrack:
                clientConnected.send("stop_ant".encode())

