#config/loader.py
import configparser

class ConfigLoader:
    def __init__(self):
        self.config = configparser.ConfigParser()

    def load(self, path):
        self.config.read(path)
        return self

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
    