#main.py
# This project
from modbus.client import Slave
from config.loader import ConfigLoader
from gui.gui import GUI
from utils.constants import ADDRESSES, UNITS

# -----------------------------------------------------------------------

# Initialize plc communications
plc = Slave("192.168.1.12")
plc.connect()

# Read current pressure units
unit = plc.get_units()

# Load test configuration
config = ConfigLoader()
config.units(unit) # Set the active units in the config to match the PLC's units

# Initialize tkinter window references Class variables `plc` and `config` (initialized above)
root = GUI(plc, config)

# Print system information to embedded console
root._log(f'System using pressure units: {unit}')

def main():
    root.mainloop()

if __name__ == "__main__":
    main()