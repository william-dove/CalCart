#cli/cli.py
import sys
from tkinter import filedialog
from calibration.calibration import CalibrationSequence

class CLI:
    '''
    This class contains all the commands the user may input to the command
    line when using the program.

    :param plc: [class Slave] Must be initialized in main prior to initializing this class.
    :param config: [class ConfigLoader] See above^.
    :param addresses: ...
    :param unit: ...
    
    '''
    def __init__(self, plc, config, ADDRESSES, unit):
        self.plc = plc # stateful reference to variable `plc` in main
        self.config = config # stateful reference to variable `config` in main
        self.ad = ADDRESSES
        self.unit = unit

    def status(self):
        '''
        Reads pressure sensor input registers.
        '''
        transducers = ['MKS 1 pressure', 'MKS 2 pressure', 'MKS 3 pressure']
        for t in transducers:
            value = self.plc.read_float(self.ad[t])
            print(f'{t}: {value:.2f} {self.unit}')

    def new_config(self):
        '''
        Automatically writes new configuration to the class ConfigLoader object, then saves it.
        
        *Changing self.config SHOULD mutate the `config = ConfigLoader()` object initialized in `main.py`
        ...but who knows. At any rate I'll just use this class attribute when running a calibration sequence
        or changing config parameters.

        :param config: class [ConfigLoader] The active configuration.
        '''
        # Set new values for the DEFAULT section
        default_values = {
            'setpoint_wait': input('Setpoint wait time [s]: '),
            'sample_rate': input('Sample rate [Hz]: '),
            'setpoint_settle': input('Setpoint settling time [s]: '), # setpoint must be within tolerance for this much time to be considered "settled"
            'setpoint_timeout': input('Setpoint timeout [s]: '),
            'num_setpoints':  input('Number of setpoints: '),
            'autotune_each': input('Would you like to autotune each setpoint? <yes>/<no>: ').lower()
        }
        for key, val in default_values.items():
            self.config.setd(key, val)

        # Set the new values for the setpoint.i sections
        for i in range(int(default_values['num_setpoints'])):
            pressure = float(input(f'Setpoint {i+1} [{self.unit}]: '))
            percent = float(input(f'Setpoint {i+1} error tolerance [%]: '))
            max_err = 0.01*percent*pressure
            self.config.set(f'setpoint.{i+1}', 'pressure', str(pressure))
            self.config.set(f'setpoint.{i+1}', 'max_err', str(max_err))

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
            self.config.save(save_path)
            print('[STATUS] Configuration saved.')

    def load_config(self):
        '''
        Loads an existing configuration.
        This can also be done when executing the program (see main.py)

        *Changing self.config SHOULD mutate the `config = ConfigLoader()` object initialized in `main.py`
        ...but who knows. At any rate I'll just use this class attribute when running a calibration sequence
        or changing config parameters.
        '''
        load_path = filedialog.askopenfilename(
            defaultextension='.ini',
            filetypes=[("INI file", "*.ini")]
        )
        self.config.load(load_path)
        print(f'[STATUS] Opened configuration file {load_path}')

    def view_config(self):
        '''
        Haven't tested yet, but this should work as expected...
        Update: it didn't.

        But now it should!
        '''
        print(self.config.print_all())


    def cal(self):
        '''
        Trying to laterally import calibration.calibration... we'll see if it works.
        '''
        cal_seq = CalibrationSequence(self.plc, self.config, self.ad, self.unit)
        results = cal_seq.run()
        # Save results
        print('[STATUS] Calibration complete. Save results...')
        saved = False
        while not saved:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes = [("comma-separated value file", "*.csv"), ("Excel file", "*.xlsx")]
            )
            if save_path.endswith(".csv"):
                results.to_csv(save_path)
                saved = True
            elif save_path.endswith(".xlsx"):
                results.to_excel(save_path)
                saved = True
            else:
                print('[WARNING] Incorrect file type.')
                continue

