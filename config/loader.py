#config/loader.py
import configparser
from io import StringIO

class ConfigLoader:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.path = None

        # Define and initialize the default values for the DEFAULT section of the config .ini
        self.default_values = {
            'setpoint_wait': '30', # [s]
            'sample_rate': '10', # [Hz]
            'setpoint_settle': '60', # [s] # setpoint must be within tolerance for this much time to be considered "settled"
            'setpoint_timeout': '300', # [s]
            'num_setpoints':  '1',
            'autotune_each': 'no'
        }
        self.setddict(self.default_values)

        # Define and initialize the default values for the first setpoint
        self.set(f'setpoint.1', 'pressure', '1') # Units set by the PLC
        self.set(f'setpoint.1', 'max_err', '0.05')

    def load(self, path):
        '''
        Overwrites existing settings with those from the given INI
        '''
        self.config.read(path)
        self.path = path
        return self
    
    def save(self, path):
        with open(path, 'w') as configfile:
            self.config.write(configfile)
        self.path = path

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
        if not self.config.has_section(section):
                self.config.add_section(section)
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
    
    def getddict(self):
        '''
        Returns a dict of the DEFAUlT section as strings
        '''
        return dict(self.config['DEFAULT'])
    
    def setddict(self, dc):
        '''
        Sets the default dict back to the DEFAULT section of the INI

        :param dc: The default dict (future: update for clarity)
        '''
        for key, val in dc.items():
            self.setd(key, val)

    def getspdicts(self):
        '''
        returns a nested dictionary of of the setpoint settings
        '''
        sps = {}
        for i in range(self.getd('num_setpoints')):
            sps[f'setpoint.{i+1}'] = dict(self.config[f'setpoint.{i+1}'])