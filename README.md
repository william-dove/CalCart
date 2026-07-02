# 2025 Calibration Cart Control System

## Overview

This project is designed to control the 2025 IMA Life Portable Vacuum Calibration Cart.

There are two levels of programming within the Cal Cart control system:

- **Lower Level Control:** A Unitronics UniStream PLC/HMI controls basic process functions such as processing sensor signals and maintaining a setpoint pressure. The user may also view real-time sensor data and execute simple tasks using the touchscreen interface on the UniStream HMI. These functions are implemented using UniLogic within `CalCart.ulpr`. UniLogic's built-in Modbus features are used to communicate with a laptop (SCADA) over Ethernet for more complex operations.

- **Higher Level Control:** The Python application within this repository is used by the SCADA to provide higher level controls. The user may develop multi-step calibration sequences and save time-dependant sensor history via the SCADA. 

This documentation will focus on the SCADA Python application providing higher level control during the calibration process. For more information on the mechanical, electrical, and lower-level control features of the Cal Cart, see the functional specification.


## Table of Contents

- Version Requirements
- Features
    - Filetree
    - Startup
    - Class Reference Heirarchy
- Usage
    - CLI Operation
    - GUI Operation
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

- Safer blocking between main thread (GUI), IO thread (CLI) and temp worker threads (CalibrationSequence)
- Ability to change pressure units from SCADA
- Print to PDF calibration report
- More status updates in GUI