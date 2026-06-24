#main.py
# This project
from modbus.client import Slave
from config.loader import ConfigLoader
from cli.cli import CLI
from calibration.calibration import CalibrationSequence
from utils.constants import ADDRESSES, UNITS, COMMANDS
# Other
import tkinter as tk
import sys
import subprocess

# -----------------------------------------------------------------------

# Initialize tkinter window
root = tk.Tk()
root.withdraw()

# Initialize plc communications
plc = Slave("192.168.1.12")
plc.connect()

# Read current pressure units
unit = plc.get_units(ADDRESSES, UNITS)
print(f'System using pressure units: {unit}')

# Load test configuration
config = ConfigLoader()
if len(sys.argv) == 2:
    config.load(sys.argv[1])
    print(f'[STATUS] Opened configuration file {sys.argv[1]}')

# Initialize command line interface
cli = CLI(plc, config)

# Command name dictionary
commands = {
    'help': lambda: print(commands.keys()),
    'status': cli.status,
    'new config': cli.new_config,
    'load config': cli.load_config,
    'cal': cli.cal,
    'stop': lambda: (plc.close(), sys.exit()),
    'cls': lambda: subprocess.run('cls', shell=True)
}

# ---------------------------------------------------------------------------------

def main():
    while True: 
        # Read commands
        command = input('(CalCart.py)>')
        cmd_func = commands.get(command)
        if cmd_func:
            cmd_func()
        else:
            print("[WARNING] Unknown command.")