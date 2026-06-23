from pymodbus.client import ModbusTcpClient
import struct
import time
import pandas as pd
from tkinter import filedialog
import tkinter as tk
import configparser
import sys
import subprocess

PLC_IP = "192.168.1.12"
slave = ModbusTcpClient(PLC_IP, timeout=3)

# Modbus address dictionary (dict key == UniLogic variable name)
ad = {
    'submit_setpoint': 0,
    'run_autotune': 1,
    'run_PID': 2,
    'MKS 1 pressure': 100,
    'MKS 2 pressure': 102,
    'MKS 3 pressure': 104,
    'MKS Zero pressure': 106,
    'Setpoint pressure': 108,
    'pressure_units': 110,
    'UUT pressure': 111
}

# Pressure units dictionary (dict key == value of pressure_units variable in UniLogic)
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
    Modbus stores 32-bit floats in two separate registers which must be "translated" 
    into a normal floating point number.
    Translates a 2-register list into a python float32.
    The order of the two registers may be swapped; this is likely the case if the numbers are all weird.
    '''
    if swapped:
            regs = regs[::-1]
    packed = struct.pack('>HH', regs[0], regs[1])
    return struct.unpack('>f', packed)[0]

def write_float(value, swapped=True):
    '''
    Performs the reverse operation of read_float.
    Translates a normal python 32-bit float into a list of two registers for Modbus.
    '''
    packed = struct.pack('>f', value)
    regs = struct.unpack('>HH', packed)
    if swapped:
            regs = regs[::-1]
    return list(regs)

def record_data(setpoint_wait, sample_rate, times, cal, uut):
    '''
    Once a setpoint is reached, samples data from the MKS 1 sensor on the cart
    as well as the unit under test at a regular sampling rate, for a designated
    amount of time.

    :param setpoint_wait: How long the system maintains and collects data at a given setpoint.
    :param sample_rate: The data sampling rate in Hz
    :param times: An existing list of times corresponding to sample points from previous setpoints. This function appends new times.
    :param cal: The existing list of sample points from previous setpoints for the MKS 1 sensor.
    :param uut: The existing list of sample points from previous setpoints for the unit under test.
    :return times: The same as the input but appended with new sample point times.
    :return cal: The same as the input but appended with new sample point pressures.
    :return uut: The same as the input but appended with new sample point pressures.
    '''
    record_start = time.time()
    while time.time() - record_start < setpoint_wait:
        # Collect data from MKS 1 sensor
        resp = slave.read_input_registers(address=ad['MKS 1 pressure'], count=2)
        if resp.isError():
            print('[WARNING] read error')
            time.sleep(1.0 / sample_rate)
            continue
        cal_value = read_float(resp.registers)
        # Collect data from UUT
        resp = slave.read_input_registers(address=ad['UUT pressure'], count=2)
        if resp.isError():
            print('[WARNING] read error')
            time.sleep(1.0 / sample_rate)
            continue
        uut_value = read_float(resp.registers)
        # Append data
        times.append(time.time())
        cal.append(cal_value)
        uut.append(uut_value)
        # Wait
        time.sleep(1.0 / sample_rate)
    return times, cal, uut

def cmd_status():
    '''
    Reads pressure sensor input registers.
    '''
    # Read pressure sensor input registers
    transducer_registers = {'MKS 1': 100, 'MKS 2': 102, 'MKS 3': 104, 'MKS Zero': 106} # This is dated and kind of redundant but I can't be bothered to change it.
    transducer_values = {}
    for t in transducer_registers:
        resp = slave.read_input_registers(address=transducer_registers[t], count=2)
        if resp.isError():
            print(f'[WARNING] {t}: read error.')
            continue
        value = read_float(resp.registers)
        transducer_values[t] = value
        print(f'{t}: {value:.2f} {unit}')

def cmd_new_config():
    '''
    Creates a new .ini configuration for the calibration sequence and saves it.
    This becomes the active configuration should a calibration sequence be started.
    
    '''
    global config
    config = configparser.ConfigParser()

    config['DEFAULT'] = {
        'setpoint_wait': input('Setpoint wait time [s]: '),
        'sample_rate': input('Sample rate [Hz]: '),
        'setpoint_settle': input('Setpoint settling time [s]: '),
    }
    num_setpoints = input('Number of setpoints: ')
    config['DEFAULT']['num_setpoints'] = num_setpoints

    for i in range(int(num_setpoints)):
        pressure = float(input(f'Setpoint {i+1} [{unit}]: '))
        percent = float(input(f'Setpoint {i+1} error tolerance [%]: '))
        max_err = 0.01*percent*pressure
        config[f'setpoint.{i+1}'] = {
             'pressure': str(pressure),
             'max_err': str(max_err)
        }
    # Save the configuration
    print('[STATUS] Finished configuring. Save the configuration file... ')
    save_path = filedialog.asksaveasfilename(
        defaultextension='.ini',
        filetypes=[("INI file", "*.ini")]
    )
    if not save_path:
        print('[STATUS] Save cancelled.')
        return
    if not save_path.endswith('.ini'):
        print('[WARNING] Configuration file not saved as .ini. Cancelling...')
        return
    else:
        with open(save_path, 'w') as configfile:
            config.write(configfile)
        print('[STATUS] Configuration saved.')

def cmd_load_config():
    '''
    Loads an existing configuration.
    This can also be done when executing the program (see main block)
    '''
    global config
    config = configparser.ConfigParser()
    load_path = filedialog.askopenfilename(
        defaultextension='.ini',
        filetypes=[("INI file", "*.ini")]
    )
    config.read(load_path)
    print(f'[STATUS] Opened configuration file {load_path}')

def cmd_cal():
    '''
    Using the parameters in the configuration file, runs a calibration sequence.
    '''
    if config is None:
        print(
            '''You need a configuration file to run the calibration sequence. 
            To make a new configuration file, use `new config`.
            To load an existing configuration, use `load config`.'''
        )
        return
    
    # Retrieve config data
    setpoint_wait = float(config['DEFAULT']['setpoint_wait'])
    sample_rate = float(config['DEFAULT']['sample_rate'])
    setpoint_settle = float(config['DEFAULT']['setpoint_settle'])
    num_setpoints = int(config['DEFAULT']['num_setpoints'])
    setpoints = []
    for i in range(num_setpoints):
        sp = float(config[f'setpoint.{i+1}']['pressure'])
        max_err = float(config[f'setpoint.{i+1}']['max_err'])
        setpoints.append((sp, max_err))

    # Begin calibration sequence
    times = []
    cal = []
    uut = []
    for sp, max_err in setpoints:
        regs = write_float(sp)
        slave.write_registers(address=ad['Setpoint pressure'], values=regs) # Write to Setpoint pressure
        # Next 3 lines mimick "Set Pressure" button on Unistream HMI
        slave.write_coil(address=ad['submit_setpoint'], value=True) # write to submit_setpoint
        time.sleep(1.0) # Wait for the submit_setpoint bit to adjust <--yay this fixed it!
        slave.write_coil(address=ad['submit_setpoint'], value=False) # reset the submit_setpoint coil (setpoint is written via positive transition contact)
        slave.write_coil(address=ad['run_PID'], value=True) # write to run_PID
        print(f'[STATUS] Adjusting pressure to setpoint ({sp} {unit})...')
        # Establish a max time in case setpoint is unreachable
        sp_timeout_time = 300 # timeout after 5 minutes
        sp_start_time = time.time()
        sp_timeout = False
        # Wait for the setpoint to settle.
        settle_start = None
        while True:
            # Read MKS 1 for PID process variable.
            resp = slave.read_input_registers(address=ad['MKS 1 pressure'], count=2)
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
            times, cal, uut = record_data(setpoint_wait, sample_rate, times, cal, uut)
            print(f'[STATUS] Finished recording for setpoint ({sp} {unit}).')
    
    df = pd.DataFrame({'time': times, 'calibration pressure': cal, 'test unit pressure': uut})

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

def cmd_stop():
    slave.close()
    sys.exit()

# Command name dictionary

commands = {
    'help': lambda: print(commands.keys()),
    'status': cmd_status,
    'new config': cmd_new_config,
    'load config': cmd_load_config,
    'cal': cmd_cal,
    'stop': cmd_stop,
    'cls': lambda: subprocess.run('cls', shell=True)
}
# ------------------------------------------

def main():
    global unit, config
    
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

    if len(sys.argv) == 2:
        config = configparser.ConfigParser()
        config.read(sys.argv[1])
        print(f'[STATUS] Opened configuration file {sys.argv[1]}')

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