# 2025 Calibration Cart Control System

## Overview

This project is designed to control the 2025 IMA Life Portable Vacuum Calibration Cart.

There are two levels of programming within the Cal Cart control system:

- **Lower Level Control:** A Unitronics UniStream PLC/HMI controls basic process functions such as processing sensor signals and maintaining a setpoint pressure. The user may also view real-time sensor data and execute simple tasks using the touchscreen interface on the UniStream HMI. These functions are implemented using UniLogic within `CalCart.ulpr`. UniLogic's built-in Modbus features are used to communicate with a laptop (SCADA) over Ethernet for more complex operations.

- **Higher Level Control:** The Python application within this repository is used by the SCADA to provide higher level controls. The user may develop multi-step calibration sequences and save time-dependant sensor history via the SCADA. 

This documentation will focus on the SCADA Python application providing higher level control during the calibration process. For more information on the mechanical, electrical, and lower-level control features of the Cal Cart, see the functional specification.


## Table of Contents

- [Version Requirements](# Version Requirements)
- [Features](# Features)
    - [Filetree](# Filetree)
    - [Startup](# Startup)
    - [Class Reference Heirarchy](# Class Reference Heirarchy)
- [Usage](# Usage)
    - [CLI Operation][#]
    - [GUI Operation][]
- Future


## Version Requirements

- Python 3.13.9
- UniLogic 1.42 rev. 220
- UniStream US5/7 firmware version 1.42.142


## Features

### Filetree

```
CalCart
+---main.py
+---calibration
¦   +---calibration.py
+---cli
¦   +---cli.py
+---config
¦   +---loader.py
+---gui
¦   +---gui.py
+---modbus
¦   +---client.py
+---old
¦   +---CalCart.py
+---utils
    +---constants.py
    +---modbus_helpers.py
```

Different functions of the application are assigned to Python Classes within designated scripts/subdirectories.

The following classes are used by `main.py` when the application is started:

- `modbus.client.Slave` (`/modbus/client.py`): Controls PLC communication.
- `config.loader.ConfigLoader` (`/config/loader.py`): Loads, saves, and accesses configuration `.ini` files to customize a calibration procedure.
- `cli.cli.CLI` (`/cli/cli.py`): Command-line interface; allows the user to quickly perform main functions using commands.
- `gui.gui.GUI` (`/gui/gui.py`): Graphical user interface; allows the user to perform all functions through a Tkinter-based graphical application.
- `utils.constants.ADDRESSES` (`/utils/constants.py`): Dictionary of Modbus addresses assigned within UniLogic for the `modbus.client.Slave` instance to reference.
- `utils.constants.UNITS` (`/utils/constants.py`): Dictionary of pressure units with the integer key they have been assigned in UniLogic; allows the user to choose between multiple pressure units.

### Startup

On startup, `main.py` completes the following actions in order:

1. An instance of `modbus.client.Slave` is created using the PLC's IP address and attemts communication by querying the value of `pressure_units` from the PLC. If successful, a message displaying the active pressure units is displayed.
2. An instance of `config.loader.ConfigLoader` is created and loads a configuration if provided.
3. An instance of `cli.cli.CLI` is created and the `Slave` and `ConfigLoader` instances are referenced as attributes of `CLI`. If the attributes are modified, the original `Slave` and `ConfigLoader` instances will also be modified (mutated)
4. An instance of `gui.gui.GUI` is created and the same `Slave` and `ConfigLoader` istances are referenced as attributes of `GUI`. Like with the CLI, if these attributes are modified, the original objects being rederenced will be mutated.
5. A worker thread is opened and waits at an input block for a user command. Inputs pass commands as methods of the `CLI` class.
6. Main loop: the program is blocked at the `GUI(tk.Tk).mainloop` method of the GUI object until the user does something on the GUI.

When the user enters the "cal" command in the CLI or clicks the "Run Calibration Sequence" button in the GUI, the calibration sequecne begins. Within `cli.py` or `gui.py`, respectively, this will create an instance of the class `calibration.calibration.CalibrationSequece`, using the attributes referencing the `Slave` and `ConfigLoader` instances. This is a stateless instance of `CalibrationSequence`, which is only referenced during that calibration procedure. When the calibration procedure is finished, the instance is discarded and the results are saved.

### Class Reference Heirarchy

Class references can be tracked along the following flow chart:

```
main.py is executed -----> `Slave` instance created        -----> `CLI` and `GUI` created (referencing -----> User loads or creates config -----> `CalibrationSequence` instance created  
                    -----> `ConfigLoader` instance created -----> `Slave` & `ConfigLoader` instances)  -----> .ini & begins calibration    ----->  using `Slave` & `ConfigLoader` references
```


## Usage

### CLI Operation

(no quotes)

```
- "help"..............: displays a list of valid commands.
- "status"............: displays the three pressure transducer readings.
- "new config"........: begins the procedure for making a new .ini using command line user inputs.
- "load config".......: loads an existing configuration from a .ini file.
- "view config".......: displays the currently active configuration options.
- "cal"...............: begins the calibration procedure.
- "stop"..............: exits the program.
- "cls"...............: clears the command promp screen.
```

### GUI Operation

The GUI should be fairly straightforward; for a more detailed description see the functional specification.


## Future

### Todo

- Safer blocking between main thread (GUI), IO thread (CLI) and temp worker threads (CalibrationSequence)
- Ability to change pressure units from SCADA
- Print to PDF calibration report
- More status updates in GUI

### Startup procedure (PLC code)

- Add in a startup screen (e.g., "would you like to begin start up process?")
- Prompt user to begin using vacuum pump (switching valves accordingly).
- Wait for MKS Zero reference to show the pressure as under 100 microns--when pressure < 100 microns, prompt user to turn on turbo pump (possibly block turbo pump power through a relay until this threshold is reached, then energize relay when pressure < 100 microns).
- Once turbo pump is running, prompt user to wait until 4 hours have passed (for the transducers to warm up--start the timer as soon as power is on), OR until pressure is low enough to zero the 3 transducers--whichever comes last.
- Once the time is up, prompt the user to zero the three transducers. Once zeroed, exit the startup mode.
Important things to have:
- Use the system time for the 4 hr timer, this way if the system gets shut off it doesn't automatically reset. Actually, probably the best way to implement this is by adding a check on startup--if the system was running less than 15 minutes ago, don't run startup, or at least make it an option to skip.

### Moving CLI into GUI

- Removing direct command line access to centralize the program in the tkinter thread.
- Create embedded terminal window in the gui

### Generate reports based on excel template

- Add information such as customer info, model number, etc. into the INI file (probably under a new section called "customer")
- Provide the option to generate a report for the calibration using this info and a default template.
- Don't let the user proceed with the calibration unless all required customer info has been entered.