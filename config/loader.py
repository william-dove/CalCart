#config/loader.py
import configparser
from io import StringIO
import os
from utils.constants import UNITS, CONVERSION

class ConfigLoader:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.path = None

        # Define and initialize the default values for the "DEFAULT" section of the config .ini
        default_values = {
            # [general]
            'setpoint_wait': '30', # [s] (general section)
            'sample_rate': '10', # [Hz] (general section)
            'setpoint_settle': '60', # [s] (general section) setpoint must be within tolerance for this much time to be considered "settled"
            'setpoint_timeout': '300', # [s] (general section)
            'num_setpoints':  '1', # (general section)
            'autotune_each': 'no', # (general section)
            'unit': 'Torr', # **Units set by the PLC**
            # [customer]
            'company': 'Company Name',
            'project': 'Project Name',
            'service_number': 'Service Number',
            'machine': 'Machine Name',
            'location': 'Location',
            'date': 'Date',
            'calibration_type': 'Calibration Type',
            'procedure': 'Procedure',
            'calibration': 'Calibration',
            # [device]
            'manufacturer': 'Manufacturer',
            'model_number': 'Model Number',
            'serial_number': 'Serial Number',
            'tag_id_number': 'Tag/ID Number',
            'range': 'Range',
            'device_accuracy': 'Device Accuracy',
            'output_signal': 'Output Signal',
            # [standard]
            'calibration_date': 'Calibration Date',
            'calibration_due_date': 'Calibration Due Date',
            'standard_accuracy': 'Standard Accuracy',
            'accuracy_ratio': 'Accuracy Ratio',
            # [setpoint.i]
            'pressure': '1', # (setpoint section) Units set by the PLC
            'max_err': '0.05'
            
        }
        for key, val in default_values.items():
            self.config['DEFAULT'][key] = val
        
        # Initialize sections of the INI (each section inherits values from DEFAULT)
        self.config.add_section('general') 
        self.config.add_section('setpoint.1') 
        self.config.add_section('customer')
        self.config.add_section('device')
        self.config.add_section('standard')
    
    # -----------------------------------------------------------------------------------------------------------------------------

    # Read/write config from file
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def load(self, path):
        '''
        Overwrites existing settings with those from the given INI
        '''
        if os.path.isfile(path):
            self.config.read(path)
            self.path = path
            return self
        else:
            raise ValueError('Configuration file not found.')
    
    def save(self, path):
        with open(path, 'w') as configfile:
            self.config.write(configfile)
        self.path = path
    
    # ----------------------------------------------------------------------------------------------------------------------------

    # Read/write config from UI
    # ~~~~~~~~~~~~~~~~~~~~~~~~~

    def get_dict(self):
        '''
        Returns a nested dictionary of the configuration.
        '''
        return {
            section: dict(self.config[section])
            for section in self.config
        }
    
    def set_dict(self, config_dict):
        '''
        Sets the config using a dict.

        :param config_dict: the new dict of strings you want to overwrite the config with.
        '''
        for section in config_dict:
            if section == 'DEFAULT':
                continue
            for key, val in config_dict[section].items():
                self.set(section, key, val)

    # --------------------------------------------------------------------------------------------------------------------------------

    # Methods for retrieving/setting values
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def get_setpoints(self):
        '''
        Gets the number of setpoints from the config file, and extracts
        useful parameters for each setpoint.

        :return setpoints: A list of tuples of the form:
        `setpoint[i] == (<setpoint i pressure>, <setpoint i error tolerance>)`
        '''
        num_setpoints = int(self.config['general']['num_setpoints'])
        setpoints = []
        for i in range(num_setpoints):
            sp = float(self.config[f'setpoint.{i+1}']['pressure'])
            max_err = float(self.config[f'setpoint.{i+1}']['max_err'])
            setpoints.append((sp, max_err))
        return setpoints
    
    def getg(self, key, cast=float):
        '''
        "get general"
        Retrieves the value for a setting under the general section of the .ini.
        This should be used whenever getting and not writing values from config.

        :param key: the key of the value
        :param cast: the type of the result
        '''
        return cast(self.config['general'][key])
    
    def setg(self, key, value):
        '''
        The reverse of getg
        This should be used whenever writing to the config.

        :param key: the key of the value
        :param value: the value (string) which you want to store
        '''
        self.config['general'][key] = value

    def get(self, section, key, cast=float):
        '''
        You get the idea.
        '''
        return cast(self.config[section][key])

    def set(self, section, key, value):
        '''
        Sets values outside of the DEFAULT section.

        :param section: the section of the .ini file you're editing
        :param key: the key of the value
        :param value: the value (string) which you want to store
        '''
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config[section][key] = value

    def getgbool(self, key, default=False):
        '''
        Retrieves a boolean from the default section.
        '''
        try:
            return self.config['general'].getboolean(key)
        except ValueError:
            print(f'[WARNING] Invalid boolean for {key}, defaulting to {default}')
            return default
        
    def getbool(self, section, key, default=False):
        '''
        Same as above for other sections.
        '''
        try:
            return self.config[section].getboolean(key)
        except ValueError:
            print(f'[WARNING] Invalid boolean for {key}, defaulting to {default}')
            return default

    # ----------------------------------------------------------------------------------------------------------------------------------

    # Setting active units
    # ~~~~~~~~~~~~~~~~~~~~

    def units(self, new_unit, old_unit=None):
        '''
        Sets the active units for the calibration sequence and alters all settings accordingly.

        Units are treated differently than other settings because changing the units requires 
        converting all setpoint pressures and tolerances to the new units. If the user wants to
        change the units without converting the setpoints, they can do so by changing the unit 
        in the config directly (e.g. `config.setg('unit', 'bar')`).

        :param new_unit: str, the new unit to set (must be one of UNITS.values())
        :param old_unit: str, the old unit to convert from (if None, will use the current unit in the config). This
            option exists to allow for changing units at the same time as other settings and handling the conversion
            after-the-fact. If the user is changing units without changing other settings, this can be left as None.
        '''
        if new_unit not in UNITS.values():
            raise ValueError(f'Invalid unit: {new_unit}. Must be one of {list(UNITS.values())}')
        
        if old_unit is None:
            old_unit = self.getg('unit', cast=str)

        # Update the setpoints in the config to reflect the new units
        for i, sp in enumerate(self.get_setpoints()):
            sp_pressure, sp_max_err = sp
            # Convert setpoint pressure to new units
            new_pressure = sp_pressure * CONVERSION[new_unit] / CONVERSION[old_unit]
            # Convert max error to new units
            new_max_err = sp_max_err * CONVERSION[new_unit] / CONVERSION[old_unit]
            # Update the setpoint in the config
            self.set(f'setpoint.{i+1}', 'pressure', str(new_pressure))
            self.set(f'setpoint.{i+1}', 'max_err', str(new_max_err))

        # Update the unit in the units section
        self.setg('unit', new_unit)


    # ----------------------------------------------------------------------------------------------------------------------------------

    # I/O and utilities
    # ~~~~~~~~~~~~~~~~~

    def print_all(self):
        '''
        Returns the whole config file as a string.
        '''
        buffer = StringIO()
        self.config.write(buffer)
        return buffer.getvalue()

    # -----------------------------------------------------------------------------------------------------------------------------------

    # (DEPRECATED)
    # ~~~~~~~~~~~~

    def getddict(self):
        '''
        Returns a dict of the DEFAUlT section as strings
        '''
        return dict(self.config['DEFAULT'])

    def getspdicts(self):
        '''
        returns a nested dictionary of of the setpoint settings
        '''
        sps = {}
        for i in range(self.getd('num_setpoints', cast=int)):
            sps[f'setpoint.{i+1}'] = dict(self.config[f'setpoint.{i+1}'])
        return sps