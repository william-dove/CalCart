#config/loader.py
import configparser
from io import StringIO
import os
from utils.constants import UNITS, CONVERSION
from config.settings import SETTINGS

class ConfigLoader:
    def __init__(self):
        '''
        Attributes:
            - .config is the actual ConfigParser object for the INI
            - .path is the path to the INI file

        Initializing `self.config["DEFAULT"]`:
            - The DEFAULT_VALUES dict currently houses all the default settings for the INI.
                In the future, I would like to just make an actual defualt INI with these
                settings, and just read that to the config. But for now this works.
        
        Initializing other sections:
            - Each other section will be used for its respective purpose and values
                will be changed accordingly. Each section actually inherits every value
                from DEFAULT, but only the ones that actually belong to that section will
                actually be read/overwritten in that respective section.
            - (See utils.constants for the description of each setting and its default value).
        '''
        self.config = configparser.ConfigParser(interpolation=None)
        self.path = None

        for s in SETTINGS:
            if s.default is not None:
                self.config['DEFAULT'][s.key] = s.default

        
        # Initialize sections of the INI (each section inherits values from DEFAULT)
        self.config.add_section('general') 
        self.config.add_section('setpoint.1') 
        # Report sections
        self.config.add_section('report.header')
        self.config.add_section('report.device')
        self.config.add_section('report.standard')
    
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
            ini_section: dict(self.config[ini_section])
            for ini_section in self.config
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
            #print(f'[WARNING] Invalid boolean for {key}, defaulting to {default}')
            return default
        
    def getbool(self, section, key, default=False):
        '''
        Same as above for other sections.
        '''
        try:
            return self.config[section].getboolean(key)
        except ValueError:
            #print(f'[WARNING] Invalid boolean for {key}, defaulting to {default}')
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
