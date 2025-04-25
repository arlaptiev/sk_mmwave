import pyautogui
import time
import subprocess

import socket
import os

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

if __name__=='__main__':
    data_folder = 'C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc\\Data'
    current_ts = None

    cwd = os.getcwd()
    print(cwd)
    resp = run_powershell(f"C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc\\DCA1000EVM_CLI_Control.exe fpga {cwd}\\cf.json")
    # print(resp.returncode)
    print(resp.stdout.decode("utf-8"))
    resp = run_powershell(f"C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc\\DCA1000EVM_CLI_Control.exe record {cwd}\\cf.json")
    # print(resp.returncode)
    print(resp.stdout.decode("utf-8"))

    
    # resp = run_powershell("C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc\\DCA1000EVM_CLI_Control.exe start_record cf.json")

    ip = '192.168.41.146' # IP address of other computer
    port = 8081
    clientSocket = socket.socket()
    clientSocket.connect((ip,port))
    print ("connected to the server!")
    i = 0
    while(True):
        print(f'About to recieve')
        dataFromServer = clientSocket.recv(64)
        print(f'Recieved {dataFromServer}')

        data = "Invalid Cmd"
        if dataFromServer == b'R':
            # reset setting
            data = "done"
            print(f'resetting')

        if dataFromServer == b'M':
            # Take a new measurement 
            print(f'Taking measurement {i}')
            i += 1
            timestamp = update_cfg_timestamp()
            # timestamp = i
            resp = run_powershell(f"C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc\\DCA1000EVM_CLI_Control.exe stop_record {cwd}\\cf.json")
            print("1: ", resp)
            resp = run_powershell_nonblocking(f"C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc\\DCA1000EVM_CLI_Record.exe start_record {cwd}\\cf.json")
            print("2: ", resp)
            time.sleep(0.5)
            pyautogui.click(40, 825) # Original
            # pyautogui.click(30, 940) # New resolution after member event
            # if resp.returncode == 0:
            # else:
            #     data = "fail"
            #     print(resp.stdout.decode("utf-8"))
            #     print(resp.stderr.decode("utf-8"))
            data = f'{timestamp}'
            # time.sleep(0.01)
            # Get timestamp of measurement
            # latest_ts = get_latest_binary(data_folder)
            # if (current_ts is None or latest_ts != current_ts) and latest_ts is not None:
            #     data = f'{latest_ts}'
            #     print(f'found ts {latest_ts}')
            #     current_ts = latest_ts
            # else:
            #     # There is no new binary, send fail
            #     print(f'no meas found')
            #     data = "fail"

        print(f'Sending {data}')
        clientSocket.send(data.encode())