# 2025 Calibration Cart Control System

## Overview

This program is designed to control the 2025 IMA Life Portable Vacuum Calibration Cart.

There are two levels of programming within the Cal Cart control system:

- **Lower Level Control:** A Unitronics UniStream PLC/HMI controls basic process functions such as processing sensor signals and maintaining a setpoint pressure. The user may also view real-time sensor data and execute simple tasks using the touchscreen interface on the UniStream HMI. These functions are implemented within UniLogic in `CalCart.ulpr`. UniLogic's built-in Modbus features are used to communicate with a laptop (SCADA) over Ethernet for more complex operations.

- **Higher Level Control:** A Python application within this repository is installed on on the SCADA to provide higher level controls. The user may develop multi-step calibration sequences and save time-dependant sensor history via the SCADA. 

This documentation will focus on the SCADA Python program providing higher level control during the calibration process. For more information on the mechanical, electrical, and lower-level control features of the Cal Cart, see the functional specification.


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
- `cli.cli.CLI` (`/cli/cli.py`): Command-line interface; contains functions that can be entered while running the application 
- `utils.constants.ADDRESSES` (`/utils/constants.py`): Dictionary of Modbus addresses assigned within UniLogic for the `modbus.client.Slave` instance to reference.
- `utils.constants.UNITS` (`/utils/constants.py`): Dictionary of pressure units with the integer key they have been assigned in UniLogic; allows the user to choose between multiple pressure units.

### Startup

On startup, `main.py` completes the following actions in order:

1. An instance of `modbus.client.Slave` is created using the PLC's IP address and attemts communication by querying the value of `pressure_units` from the PLC. If successful, a message displaying the active pressure units is displayed.
2. An instance of `config.loader.ConfigLoader` is created and loads a configuration if provided.
3. An instance of `cli.cli.CLI` is created and the `Slave` and `ConfigLoader` instances are referenced as attributes of `CLI`. If the attributes are modified, the original `Slave` and `ConfigLoader` instances will also be modified (mutated)
4. Main loop: the program waits at an input block for a user command, and passes commands as methods of the `CLI` class.

When the user enters the "cal" command, `main.py` calls `CLI.cal()`. Within `cli.py`, this will create an instance of the class `calibration.calibration.CalibrationSequece`, using the `CLI` attributes referencing the `Slave` and `ConfigLoader` instances. `CLI.cal()` creates a stateless instance of `CalibrationSequence`, which is only referenced during that calibration procedure. When the calibration procedure is finished, the instance is discarded and the user is prompted to save the results.

### Class Reference Heirarchy

Class references can be tracked along the following flow chart:

```
main.py is executed -----> `Slave` instance created        -----> `CLI` instance created (referencing ----> 
                    -----> `ConfigLoader` instance created -----> `Slave` & `ConfigLoader` instances) ----> 

---------------------------------------------------------------------------------------------------------

---> User loads or creates config ----> `CalibrationSequence` instance created    
---> .ini & enters "cal" command  ---->  using `Slave` & `configloader` references

```


## Usage

### CLI Operation

The user may enter the following commands (no quotes):

- "help".........: displays a list of valid commands.
- "status".......: displays the three pressure transducer readings.
- "new config"...: begins the procedure for making a new .`ini` using command line user inputs.
- "load config"..: loads an existing configuration from a `.ini` file.
- "view config"..: displays the currently active configuration options.
- "cal"..........: begins the calibration procedure.
- "stop".........: exits the program.
- "cls"..........: clears the command promp screen.

### GUI Operation

(incomplete)


## Future

- working GUI