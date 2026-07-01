#cli/cli.py
from tkinter import filedialog
from calibration.calibration import CalibrationSequence
import os
import threading

class CLI:
    '''
    This class contains all the commands the user may input to the command
    line when using the program.

    __init__ parameters:
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
        '''
        config_dict = {}
        # Set new values for the DEFAULT section
        print('----------General Settings----------')
        config_dict['general'] = {
            'setpoint_wait': input('1. Setpoint wait time [s]: '),
            'sample_rate': input('2. Sample rate [Hz]: '),
            'setpoint_settle': input('3. Setpoint settling time [s]: '), # setpoint must be within tolerance for this much time to be considered "settled"
            'setpoint_timeout': input('4. Setpoint timeout [s]: '),
            'num_setpoints':  input('5. Number of setpoints: '),
            'autotune_each': input('6. Autotune each setpoint? <yes>/<no>: ').lower()
        }

        # Set the new values for the setpoint.i sections
        print('----------Setpoint Settings----------')
        num_setpoints = int(config_dict['general']['num_setpoints'])
        for i in range(num_setpoints):
            pressure = float(input(f'Setpoint {i+1} [{self.unit}]: '))
            percent = float(input(f'Setpoint {i+1} error tolerance [%]: '))
            max_err = 0.01*percent*pressure
            config_dict[f'setpoint.{i+1}'] = {
                'pressure': str(pressure),
                'max_err': str(max_err)
            }

        # Save the configuration
        self.config.set_dict(config_dict)
        print('[STATUS] Finished configuring. Enter save directory/filename (*.ini):')
        # save_path = filedialog.asksaveasfilename(
        #     defaultextension='.ini',
        #     filetypes=[("INI file", "*.ini")]
        # )
        saved = False
        while not saved:
            save_path = input('>')
            save_dir, save_filename = os.path.split(save_path)
            if os.path.isdir(save_dir) and save_filename.endswith('.ini'):
                self.config.save(save_path)
                print('[STATUS] Configuration saved.')
                saved = True
            else:
                print('[WARNING] Invalid path or configuration file not saved as .ini.')

    def load_config(self):
        '''
        Loads an existing configuration.
        This can also be done when executing the program (see main.py)

        *Changing self.config SHOULD mutate the `config = ConfigLoader()` object initialized in `main.py`
        ...but who knows. At any rate I'll just use this class attribute when running a calibration sequence
        or changing config parameters.
        '''
        print('Enter a configuration file directory:')
        # load_path = filedialog.askopenfilename(
        #     defaultextension='.ini',
        #     filetypes=[("INI file", "*.ini")]
        # )
        load_path = input('>')
        if os.path.isfile(load_path) and load_path.endswith('.ini'):
            self.config.load(load_path)
            print(f'[STATUS] Opened configuration file {load_path}')
        else:
            print(f'[WARNING] No such configuration file {load_path}')

    def view_config(self):
        '''
        Haven't tested yet, but this should work as expected...
        Update: it didn't.

        But now it should!
        '''
        print(self.config.path)
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

    # ----------------------------------------------------------------------------------------------------------------------

    # Everything below should be unnecessary.
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # I thought I would need to do the same thing I did to the GUI, i.e. run the calibration sequence
    # on a worker thread to avoid blocking the main thread, which is now burdened with keeping the tkinter
    # gui running. However, I forgot that I already sent all cli stuff to another thread executing `main.ioloop()`,
    # which is totally ok to block while executing longer functions like the calibration sequence. That being said,
    # I'm still going to leave everything below commented out since I think it's good practice to open worker threads
    # for stuff like this and it *should* work as written. However, as they say, if it ain't broke don't fix it--so
    # for the time being I'm going to stick to the method above.

    # def cal(self):
    #     '''
    #     Opens a worker thread to run the calibration sequence.
    #     Will need to use the same method for printing messages to the console
    #     while this is running.
    #     '''
    #     # Enter save path for when finished.
    #     print('Enter a save directory/filename for the results (*.csv, *.xlsx):')
    #     saved = False
    #     while not saved:
    #         save_path = input('>')
    #         save_dir, save_filename = os.path.split(save_path)
    #         if os.path.isdir(save_dir):
    #             if save_filename.endswith('.xlsx') or save_filename.endswith('.csv'):
    #                 self._resultspath = save_path
    #                 saved=True
    #         else:
    #             print('[WARNING] Invalid path or configuration file not saved as .ini.')

    #     # Begin calibration
    #     print('[cli]\n') # Temporary fix for messages popping up during the cli input loop (same as GUI)

    #     threading.Thread(
    #         target=self._run_calibration,
    #         daemon=True
    #     ).start()

    # def _run_calibration(self):
    #     '''
    #     Runs the calibration sequence in a new thread.
    #     When complete, activates callback function `._cal_finished`.
    #     '''
    #     try:
    #         cal_seq = CalibrationSequence(
    #             self.plc,
    #             self.config,
    #             self.ad,
    #             self.unit
    #         )

    #         results = cal_seq.run()

    #         save_path = self._resultspath

    #         if save_path.endswith(".csv"):
    #             results.to_csv(save_path, index=False)
    #         elif save_path.endswith(".xlsx"):
    #             results.to_excel(save_path, index=False)

    #     except Exception as e:
    #         print(f"[ERROR] {e}")

    # def _message(self, msg):
    #     '''
    #     Prints a message while the input loop is active.
    #     '''
    #     print('[cli]\n' + msg + '\n(CalCart.py)>')