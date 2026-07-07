#main.py
# This project
from modbus.client import Slave
from config.loader import ConfigLoader
from cli.cli import CLI
from gui.gui import GUI
from utils.constants import ADDRESSES, UNITS
# Other
import tkinter as tk
import sys

# -----------------------------------------------------------------------

# Initialize plc communications
plc = Slave("192.168.1.12")
plc.connect()

# Read current pressure units
unit = plc.get_units(ADDRESSES, UNITS)
#print(f'System using pressure units: {unit}')

# Load test configuration
config = ConfigLoader()
# if len(sys.argv) == 2:
#     config.load(sys.argv[1])
#     print(f'[STATUS] Opened configuration file {sys.argv[1]}')

# Initialize tkinter window references Class variables `plc` and `config` (initialized above)
root = GUI(plc, config, ADDRESSES, unit)
# # Initialize command line interface - references Class variables `plc` and `config` (initialized above)
# cli = CLI(plc, config, ADDRESSES, unit)

root._log(f'System using pressure units: {unit}')

# # Define shutdown protocol # !! This is done in GUI now
# def shutdown():
#     '''
#     Safely closes the program. Activated either by the red X in the GUI
#     or the `stop` command in the CLI.

#     * I'm not sure how the `stop` command will function now that CLI commands are 
#     being executed on a separate thread. Maybe it will still work?
#     '''
#     plc.close()
#     root.quit()
#     root.destroy()
#     sys.exit()
# root.protocol("WM_DELETE_WINDOW", shutdown)

# # Command name dictionary
# commands = {
#     'help': lambda: print(commands.keys()),
#     'status': cli.status,
#     'new config': cli.new_config,
#     'load config': cli.load_config,
#     'view config': cli.view_config,
#     'cal': cli.cal, # creates a local CalibrationSequence() object as an attribute within the cli or gui.
#     'stop': shutdown,
#     'cls': lambda: subprocess.run('cls', shell=True)
# }

# ---------------------------------------------------------------------------------
# def ioloop():
#     '''
#     Everything executed from the command line executes here, while the 
#     main thread is busy running tkinter.

#     Eventually I might move command execution to the main thread,
#     but for the time being this seems to work fine and the main thread
#     is already busy with the gui.
#     '''
#     while True: 
#         # Read commands
#         command = input('(CalCart.py)>')
#         # If a process is running from the gui, don't interpret the command
#         if root.is_busy:
#             print('Calibration in progress, please wait...')
#         else:
#             cmd_func = commands.get(command)
#             if cmd_func:
#                 cmd_func()
#             else:
#                 print("[WARNING] Unknown command.")

def main():
    # threading.Thread(
    #     target=ioloop, 
    #     daemon=True
    # ).start()
    root.mainloop()

if __name__ == "__main__":
    main()