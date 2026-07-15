#calibration/calibration.py
import time
import pandas as pd
import numpy as np
import xlwings as xw
import os
from utils.constants import ADDRESSES
from config.settings import SETTINGS

# Defines the calibration sequence.

class CalibrationSequence:
    '''
    A stateless class which is instantiated within the `GUI` to execute a calibration sequence.
    After the calibration is complete, the instance is discarded.

    __init__ parameters:
    :param plc: class Slave
    :param config: class ConfigLoader
    :param addresses: dict of Modbus addresses assigned by PLC
    :param log_callback: callable used to emit status messages in the Tk main thread.
    '''
    def __init__(self, plc, config, log_callback, prompt_callback=None):
        '''
        Initialize object references.
            - `log_callback` is a method of the `GUI` class, which is called here
                to print updates to the console during calibration.
            - `prompt_callback` allows the GUI to provide a pressure input dialog
                from the Tk main thread when manual UUT entry is enabled.

        Determine units from config.
        '''
        self.plc = plc
        self.config = config
        self.ad = ADDRESSES # dictionary of addresses. The only reason it's `ad`` and not `addresses` is because I'm lazy.
        self.log = log_callback
        self.prompt = prompt_callback

        self.unit = self.config.getg('unit', cast=str)

    def run(self):
        '''
        Runs a calibration sequence using the plc and config specified during instantiation.

        :return: dataframe containing results of calibration sequence.
        '''
        self.log('[STATUS] Starting calibration...')

        setpoints = self.config.get_setpoints() # list of tuples of form (<setpoint pressure>, <setpoint error tolerance>)

        columns = ['setpoint', 'setpoint pressure', 'setpoint max error', 'reference/standard pressure']
        if self.config.getgbool('uut_signal'):
            columns.append('uut signal [V]')
        if self.config.getgbool('manual_entry'):
            for n in range(self.config.getg('num_test_units', cast=int)):
                columns.append(f'uut {n+1}')

        df = pd.DataFrame(columns=columns)
        df.set_index('setpoint', inplace=True)

        # Build results list
        for i, sp in enumerate(setpoints):
            i+=1 # Setpoints start counting at 1
            pressure, max_err = sp

            # Keep track of setpoint info
            df.loc[i, 'setpoint pressure'] = pressure
            df.loc[i, 'setpoint max error'] = max_err

            self._prep_setpoint(pressure)

            if self.config.getgbool('autotune_each'):
                self._autotune()
            else:
                self._check_autotune()

            settled = self._set_pressure(pressure, max_err)
            if not settled:
                self.log(f'[STATUS] Skipping setpoint ({sp} {self.unit})')
                continue

            if self.config.getgbool('manual_entry'):
                values = self._get_user_input()
                for n in range(self.config.getg('num_test_units', cast=int)):
                    df.loc[i, f'uut {n+1}'] = values[n]
            
            ref_pressure, uut_signal = self._record()
            df.loc[i, 'reference/standard pressure'] = ref_pressure
            if self.config.getgbool('uut_signal'):
                df.loc[i, 'uut signal [V]'] = uut_signal


        # Save results
        self.log('[STATUS] Calibration sequence complete!')
        self.results = df
        return self.results
    
    def save_results(self, resultsdir):
        '''
        Saves the raw results as an excel file.

        **FUTURE** I might also provide an option to save the raw data as a csv.
        '''
        save_path = os.path.join(resultsdir, 'results.xlsx')
        self.results.to_excel(save_path, index=True)

    def generate_report(self, resultsdir, results: pd.DataFrame = None):
        '''
        Makes a PDF report after running a calibration sequence from the GUI.

        Currently saves an excel file, not a PDF.
        Currently only works with one UUT. Raw UUT signal is not 
        included in the report.
        Doesn't yet include UUT error, though this should be si,ple
        enough to implement.

        :param resultsdir: The directory to save the report.
        :param resuts: Optional excel file to get results from. If
            none is provided, the most recent result stored in the 
            `self.results` attribute is used.
        '''
        if results is None:
            results = self.results

        def fill():
            with xw.App(visible=False) as app:
                wb = app.books.open('calibration/template.xltx')
                ws = wb.sheets['Sheet1']

                # Fill in header info
                for s in SETTINGS:
                    if s.report_cell is not None:
                        val = self.config.get(s.section, s.key, cast=str)
                        cell = s.report_cell
                        ws[cell].value = val

                # Fill in setpoint results (currently for 1 UUT only.)
                report_row = 60 # The "setpoint" column in the report is in cells A60:A70,
                                # The "standard" column is B60:B70, and the "instrument"
                                # column is C60:C70.
                for sp_num, row in results.iterrows():
                    sp_cell = f'A{report_row}'
                    std_cell = f'B{report_row}'
                    inst_cell = f'C{report_row}'

                    ws[sp_cell].value = sp_num
                    ws[std_cell].value = row['reference/standard pressure']
                    ws[inst_cell].value = row['uut 1']

                    report_row += 1

                save_path = os.path.join(resultsdir, 'report.xlsx')
                wb.save(save_path)

        try:
            fill()
        except Exception as e:
            self.log(f'[ERROR] {e}.\nFailed to open Excel file. Check if the file is already open in Excel.')

    # ----------------------------------------------------------------------------------------------------------------------------


    # Helpers
    # ~~~~~~~

    def _prep_setpoint(self, sp):
        '''
        Communicates with the PLC to apply a setpoint.
        Basically mimicks "Set Pressure" button on UniStream HMI.

        :param sp: the setpoint pressure.
        '''
        self.log(f'[STATUS] Submitting setpoint ({sp} {self.unit})...')
        self.plc.write_float(self.ad['Setpoint pressure'], sp)
        self.plc.write_coil(self.ad['submit_setpoint'], value=True)
        time.sleep(1.0) # Wait for the submit_setpoint bit to adjust <--yay this fixed it!
        self.plc.write_coil(self.ad['submit_setpoint'], value=False)

    def _check_autotune(self):
        autotune_complete = self.plc.read_coil(self.ad['PID Configuration.Autotune Done'])
        if autotune_complete:
            self.log(f'[STATUS] Autotune already completed for this calibration sequence.')
            return
        else:
            self.log('[STATUS] No autotune parameters found.')
            self._autotune()

    def _autotune(self):
        '''
        Completes an autotune sequence at the current setpoint.
        This function assumes that a setpoint has already been set by toggling
        the submit_setpoint bit.

        :return: False for failure and True for success
        '''
        self.log('[STATUS] Autotuning...')
        self.plc.write_coil(self.ad['run_PID'], value=False) # (experimental) this may not do anything but it couldn't hurt and might be good
        self.plc.write_coil(self.ad['run_autotune'], value=True)
        
        timeout = time.time() + 600 # 10 min timeout--should be enough but if the autotune isn't finishing by then I can change

        time.sleep(1.0) # Let the system start the autotune process before querying if it is complete.

        autotune_complete = False
        while not autotune_complete:
            if time.time() > timeout:
                raise RuntimeError('Autotune timeout')
            autotune_complete = self.plc.read_coil(self.ad['PID Configuration.Autotune Done'])
            time.sleep(1.0)
        self.log('[STATUS] Autotune complete.')

    def _set_pressure(self, sp, max_err):
        '''
        :return: True for successful settling, False for timeout.
        '''
        self.log(f'[STATUS] Attempting to reach setpoint ({sp} {self.unit})...')
        self.plc.write_coil(self.ad['run_PID'], value=True)

        # Establish a max time in case setpoint is unreachable
        sp_timeout = False
        setpoint_timeout = self.config.getg('setpoint_timeout')
        timeout = time.time() + setpoint_timeout # 10 minute timeout rn

        # Wait for the setpoint to settle.
        setpoint_settle = self.config.getg('setpoint_settle') # how long the setpoint must be stable to begin data collection.
        settle_start = None
        while True:
            # Check for timeout
            if time.time() > timeout:
                self.log(f'[WARNING] Setpoint is unreachable after {setpoint_timeout}s')
                return False

            # Read MKS 1 for PID process variable.
            pv = self.plc.read_float(self.ad['MKS 1 pressure']) # process variable

            # Check if the setpoint is settled.
            err = abs(pv - sp) # deviation from setpoint pressure
            if err <= max_err: # inside tolerance
                if settle_start is None:
                    settle_start = time.time()

                elapsed = time.time() - settle_start

                if elapsed >= setpoint_settle:
                    self.log(f'[STATUS] Settled. Collecting data for setpoint ({sp} {self.unit})...')
                    return True
            else:
                # reset timer if tolerance band is exceeded.
                settle_start = None

            time.sleep(0.01) # a 100Hz sample rate seemed to work alright for settling time.

    def _get_user_input(self):
        '''
        Prompts the operator for the measured pressure for each unit under test.
        '''
        num_units = self.config.getg('num_test_units', cast=int)
        values = []

        for n in range(num_units):
            prompt_text = f'Enter UUT {n+1} pressure ({self.unit})'
            self.log(f'[STATUS] Waiting for UUT {n+1} pressure...')
            
            value = self.prompt(prompt_text)
            
            values.append(float(value) if value is not None else np.nan)

        return values

    def _record(self):
        '''
        Once a setpoint is reached, samples data from the MKS 1 sensor on the cart
        as well as the unit under test at a regular sampling rate, for a designated
        amount of time.

        If manual entry is selected, the pressure is not recorded until the user enters the 
        measured pressure for each unit under test. It is reccomended to select a short 
        wait time, so that data is recorded only directly after the user enters the uut
        measurement--these values should theoretically be taken at the exact same time.

        **FUTURE** I should add a buffer of reference measurements, maybe on yet another
        thread; this way the the system can just grab the exact measurement averaged around
        the exact time point that the user enters the uut pressure, and the reference/uut
        measurements are compared at exactly the same time. 

        :return ref_pressure: pressure recorded from the cal cart's reference transducer.
        :return uut_signal: If a device is plugged into the PLC input reserved for a uut device,
            the raw signal is recorded. Otherwise this value returns None.
        '''
        # Check settings for how long to record, sampling rate, and whether to collect a uut signal
        setpoint_wait = self.config.getg('setpoint_wait')
        sample_rate = self.config.getg('sample_rate')
        uut_connected = self.config.getgbool('uut_signal')

        # Make lists to keep track of data
        ref_pressures = []
        uut_signals = []

        # Start recording and keep track of time
        record_start = time.time()
        while time.time() - record_start < setpoint_wait:
            # Collect data from MKS 1 sensor
            p = self.plc.read_float(self.ad['MKS 1 pressure'])
            ref_pressures.append(p)
            # Collect data from uut
            if uut_connected:
                u = self.plc.read_float(self.ad['UUT pressure'])
                uut_signals.append(u)
            # Wait
            time.sleep(1.0 / sample_rate)

        ref_pressure = np.mean(np.array(ref_pressures))
        if uut_connected:
            uut_signal = np.mean(np.array(uut_signals))
        else:
            uut_signal = None
        
        return ref_pressure, uut_signal
