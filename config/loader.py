#config/loader.py
import configparser
from io import StringIO

class ConfigLoader:
    def __init__(self):
        self.config = configparser.ConfigParser()

    def load(self, path):
        self.config.read(path)
        return self
    
    def save(self, path):
        with open(path, 'w') as configfile:
            self.config.write(configfile)

    def get_setpoints(self):
        '''
        Gets the number of setpoints from the config file, and extracts
        useful parameters for each setpoint.

        :return setpoints: A list of tuples of the form:
        `setpoint[i] == (<setpoint i pressure>, <setpoint i error tolerance>)`
        '''
        num_setpoints = int(self.config['DEFAULT']['num_setpoints'])
        setpoints = []
        for i in range(num_setpoints):
            sp = float(self.config[f'setpoint.{i+1}']['pressure'])
            max_err = float(self.config[f'setpoint.{i+1}']['max_err'])
            setpoints.append((sp, max_err))
        return setpoints
    
    def getd(self, key, cast=float):
        '''
        Retrieves the value for a setting under the DEFAULT section of the .ini.
        This should be used whenever getting and not writing values from config.

        :param key: the key of the value
        :param cast: the type of the result
        '''
        return cast(self.config['DEFAULT'][key])
    
    def setd(self, key, value):
        '''
        The reverse of get_default.
        This should be used whenever writing to the config.

        :param key: the key of the value
        :param value: the value (string) which you want to store
        '''
        self.config['DEFAULT'][key] = value

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
        self.config[section][key] = value

    def getdbool(self, key, default=False):
        '''
        Retrieves a boolean from the default section.
        '''
        try:
            return self.config['DEFAULT'].getboolean(key)
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
        
    def print_all(self):
        buffer = StringIO()
        self.config.write(buffer)
        return buffer.getvalue()