#cli/cli.py
import sys
from tkinter import filedialog

class CLI:
    '''
    This class contains all the commands the user may input to the command
    line when using the program.

    :param plc: [class Slave] Must be initialized in main prior to initializing this class.
    :param config: [class ConfigLoader] See above^.
    :param addresses: ...
    :param unit: ...
    
    '''
    def __init__(self, ADDRESSES, unit):
        self.ad = ADDRESSES,
        self.unit = unit

    def status(self, plc):
        '''
        Reads pressure sensor input registers.
        '''
        transducers = ['MKS 1 pressure', 'MKS 2 pressure', 'MKS 3 pressure']
        for t in transducers:
            value = plc.read_float(self.ad[t])
            print(f'{t}: {value:.2f} {self.unit}')

    def new_config(self, config):
        '''
        Automatically writes new configuration to the class ConfigLoader object, then saves it.

        :param config: class [ConfigLoader] The active configuration.
        '''
        config['DEFAULT'] = {
            'setpoint_wait': input('Setpoint wait time [s]: '),
            'sample_rate': input('Sample rate [Hz]: '),
            'setpoint_settle': input('Setpoint settling time [s]: '), # setpoint must be within tolerance for this much time to be considered "settled"
            'setpoint_timeout': input('Setpoint timeout [s]: ')
        }
        num_setpoints = input('Number of setpoints: ')
        config['DEFAULT']['num_setpoints'] = num_setpoints
        autotune_each = input('Would you like to autotune each setpoint? <yes>/<no>').lower()
        if autotune_each == 'yes':
            config['DEFAULT']['autotune_each'] = 'yes'
        else: # Default to 'no'
            config['DEFAULT']['autotune_each'] = 'no'

        for i in range(int(num_setpoints)):
            pressure = float(input(f'Setpoint {i+1} [{self.unit}]: '))
            percent = float(input(f'Setpoint {i+1} error tolerance [%]: '))
            max_err = 0.01*percent*pressure
            config[f'setpoint.{i+1}'] = {
                'pressure': str(pressure),
                'max_err': str(max_err)
            }
        # Save the configuration
        print('[STATUS] Finished configuring. Save the configuration file... ')
        save_path = filedialog.asksaveasfilename(
            defaultextension='.ini',
            filetypes=[("INI file", "*.ini")]
        )
        if not save_path:
            print('[STATUS] Save cancelled.')
            return
        elif not save_path.endswith('.ini'):
            print('[WARNING] Configuration file not saved as .ini. Cancelling...')
            return
        else:
            with open(save_path, 'w') as configfile:
                config.write(configfile)
            print('[STATUS] Configuration saved.')

    def load_config(self, config):
        '''
        Loads an existing configuration.
        This can also be done when executing the program (see main.py)
        '''
        load_path = filedialog.askopenfilename(
            defaultextension='.ini',
            filetypes=[("INI file", "*.ini")]
        )
        config.read(load_path)
        print(f'[STATUS] Opened configuration file {load_path}')

    def cal(self):
        '''
        Still need to do this, not quite sure how.
        '''
        return

