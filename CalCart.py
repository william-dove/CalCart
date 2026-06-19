from pymodbus.client import ModbusTcpClient
import struct
import time
import pandas as pd
from tkinter import filedialog
import tkinter as tk



PLC_IP = "192.168.1.12"
slave = ModbusTcpClient(PLC_IP, timeout=3)
units = {
    0: 'Torr',
    1: 'micron',
    2: 'bar',
    3: 'mbar',
    4: 'Pascal',
    5: 'kPa'
}

# --------------------------------------- 

def read_float(regs, swapped=True):
    '''
    Translates a Modbus 32-bit float from a 2-register list into a usable number.
    The register bits may be in a reverse order; if the numbers are all weird this is likely why.
    '''
    if swapped:
            regs = regs[::-1]
    packed = struct.pack('>HH', regs[0], regs[1])
    return struct.unpack('>f', packed)[0]
def write_float(value, swapped=True):
    '''
    Translates a f32-bit float into the proper 2-register format for Modbus.
    '''
    packed = struct.pack('>f', value)
    regs = struct.unpack('>HH', packed)
    if swapped:
            regs = regs[::-1]
    return list(regs)

def record_data(setpoint_wait, sample_rate, times, values):
    record_start = time.time()
    while time.time() - record_start < setpoint_wait:
        resp = slave.read_input_registers(address=100, count=2)
        if resp.isError():
            print('[WARNING] read error')
            time.sleep(1.0 / sample_rate)
            continue
        value = read_float(resp.registers)
        times.append(time.time())
        values.append(value)
        time.sleep(1.0 / sample_rate)
    return times, values


def cmd_stop():
    slave.close()
    exit()
def cmd_status():
    # Read pressure sensor input registers
    transducer_registers = {'MKS 1': 100, 'MKS 2': 102, 'MKS 3': 104, 'MKS Zero': 106}
    transducer_values = {}
    for t in transducer_registers:
        resp = slave.read_input_registers(address=transducer_registers[t], count=2)
        if resp.isError():
            print(f'[WARMING] {t}: read error.')
        value = read_float(resp.registers)
        transducer_values[t] = value
        print(f'{t}: {value:.2f} {unit}')

def cmd_cal():
    setpoint_wait = float(input('Setpoint wait time [s]: '))
    sample_rate = float(input('Sample rate [Hz]: '))
    setpoint_settle = float(input('Setpoint settling time [s]: '))
    num_setpoints = int(input('Number of setpoints: '))
    setpoints = []
    for i in range(num_setpoints):
        sp = float(input(f'Setpoint {i+1} [{unit}]: '))
        percent = float(input(f'Setpoint {i+1} error tolerance [%]'))
        max_err = 0.01*percent*sp
        setpoints.append((sp, max_err))

    input('press ENTER to begin calibration')

    times = []
    values = []
    for sp, max_err in setpoints:
        regs = write_float(sp)
        slave.write_registers(address=108, values=regs) # Write to Setpoint pressure
        # Next 3 lines mimick "Set Pressure" button on Unistream HMI
        slave.write_coil(address=0, value=True) # write to submit_setpoint
        slave.write_coil(address=2, value=True) # write to run_PID
        slave.write_coil(address=0, value=False) # reset the submit_setpoint coil (setpoint is written via positive transition contact)
        print(f'[STATUS] Adjusting pressure to setpoint ({sp} {unit})...')
        # Establish a max time in case setpoint is unreachable
        sp_timeout_time = 300 # timeout after 5 minutes
        sp_start_time = time.time()
        sp_timeout = False
        # Wait for the setpoint to settle.
        settle_start = None
        while True:
            # Read MKS 1 for PID process variable.
            resp = slave.read_input_registers(address=100, count=2)
            if resp.isError():
                print('[WARNING] read error')
                continue
            pv = read_float(resp.registers) # process variable

            # Check for timeout
            sp_elapsed_time = time.time() - sp_start_time
            if sp_elapsed_time > sp_timeout_time:
                print(f'[WARNING] Setpoint is unreachable after {sp_timeout_time}s; Skipping setpoint.')
                sp_timeout = True
                break
            # Check if the setpoint is settled.
            err = abs(pv - sp) # deviation from setpoint pressure
            if err <= max_err:
                # inside tolerance
                if settle_start is None:
                    settle_start = time.time()

                elapsed = time.time() - settle_start

                if elapsed >= setpoint_settle:
                    print(f'[STATUS] Settled. Collecting data for setpoint ({sp} {unit})...')
                    break
            else:
                # reset timer if tolerance band is exceeded.
                settle_start = None

            time.sleep(1.0 / sample_rate)

        # If settled, collect data for the setpoint; else move on to next setpoint.
        if sp_timeout:
            continue
        else:
            times, values = record_data(setpoint_wait, sample_rate, times, values)
            print(f'[STATUS] Finished recording for setpoint ({sp} {unit}).')
    
    df = pd.DataFrame({'time': times, 'pressure': values})

    print('[STATUS] Calibration complete. Save results...')
    saved = False
    while not saved:
        save_path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[("comma-separated value file", "*.csv"), ("Excel file", "*.xlsx")]
        )
        if save_path.endswith('.csv'):
            df.to_csv(save_path)
            saved = True
        elif save_path.endswith('.xlsx'):
            df.to_excel(save_path)
            saved = True
        else:
            print('[WARNING] Incorrect file type.')
            continue


# Command name dictionary

commands = {
    'stop': cmd_stop,
    'status': cmd_status,
    'cal': cmd_cal,
    'help': lambda: print(commands.keys())
}
# ------------------------------------------

def main():
    global unit
    
    root = tk.Tk()
    root.withdraw()
    
    if not slave.connect():
        raise ConnectionError("Failed to connect to PLC")

    resp = slave.read_input_registers(address=110, count=1) # reading 16-bit Ints should be easy?
    if resp.isError():
        print(f"Modbus error: {resp}")
    else:
        #print(resp.registers)  # debug
        units_idx = resp.registers[0]
        unit = units[units_idx]
        print(f'System using pressure units: {unit}')

    while True: 
        # Read commands
        command = input('(CalCart.py)>')
        cmd_func = commands.get(command)
        if cmd_func:
            cmd_func()
        else:
            print("[WARNING] Unknown command.")

if __name__ == "__main__":
    main()