#config/loader.py
import configparser
from io import StringIO
import os

class ConfigLoader:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.path = None

        # Define and initialize the default values for the "DEFAULT" section of the config .ini
        default_values = {
            'setpoint_wait': '30', # [s] (general section)
            'sample_rate': '10', # [Hz] (general section)
            'setpoint_settle': '60', # [s] (general section) setpoint must be within tolerance for this much time to be considered "settled"
            'setpoint_timeout': '300', # [s] (general section)
            'num_setpoints':  '1', # (general section)
            'autotune_each': 'no', # (general section)
            'pressure': '1', # (setpoint section) Units set by the PLC
            'max_err': '0.05'
        }
        for key, val in default_values.items():
            self.config['DEFAULT'][key] = val
        
        # Initialize sections of the INI
        self.config.add_section('general') # Inherits values from DEFAULT
        self.config.add_section('setpoint.1') # inherits values from DEFAULT
    
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

    # Methods for retrieving values
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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