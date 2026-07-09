#main.py
# This project
from modbus.client import Slave
from config.loader import ConfigLoader
from gui.gui import GUI
from utils.constants import ADDRESSES, UNITS

# -----------------------------------------------------------------------

def main():

    # Initialize plc communications
    plc = Slave("192.168.1.12")

    try:
        plc.connect()
        unit = plc.get_units() # Read current pressure units
    except Exception as e:
        print(e)

    # Load test configuration
    config = ConfigLoader()

    if plc.connected:
        config.units(unit) # Set the active units in the config to match the PLC's units

    # Initialize tkinter window references Class variables `plc` and `config` (initialized above)
    root = GUI(plc, config)

    # Print system information to embedded console
    if plc.connected:
        root.log(f'Connected to PLC.')
        root.log(f'System using pressure units: {unit}')
    else:
        root.log(f'PLC connection failed. Operating in offline mode.')

    root.mainloop()

if __name__ == "__main__":
    main()