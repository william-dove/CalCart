#calibration/calibration.py
import time
import pandas as pd
from tkinter import filedialog

# Defines the calibration sequence.

class CalibrationSequence:
    def __init__(self, plc, config, ADDRESSES, unit):
        '''
        :param plc: class Slave
        :param config: class ConfigLoader
        :param addresses: dict of Modbus addresses assigned by PLC
        :param units: str (pressure unit)
        '''
        self.plc = plc # class Slave (defined in `client.py`)
        self.config = config
        self.ad = ADDRESSES # dictionary of addresses. The only reason it's `ad`` and not `addresses` is because I'm lazy.
        self.unit = unit

    def run(self):
        '''
        Runs a calibration sequence using the plc and config specified during initialization.

        :return: dataframe containing results of calibration sequence.
        '''
        print('[STATUS] Starting calibration...')
        setpoints = self.config.get_setpoints() # list of tuples of form (<setpoint pressure>, <setpoint error tolerance>)
        times, cal, uut = [], [], [] # Initialize lists for storing results

        # Build results list
        for sp, max_err in setpoints:
            self._apply_setpoint(sp)
            self._check_autotune()
            settled = self._set_pressure(sp, max_err)
            if settled:
                times, cal, uut = self._record_data(times, cal, uut)
                print(f'[STATUS] Finished recording for setpoint ({sp} {self.unit}).')
            else:
                print(f'[STATUS] Skipping setpoint ({sp} {self.unit})')
                continue
        
        # Save results
        return pd.DataFrame({'time': times, 'calibration pressure': cal, 'test unit pressure': uut})
        
    # ----------------------------------------------------------------------------------------------------------------------------

    def _apply_setpoint(self, sp):
        '''
        Communicates with the PLC to apply a setpoint.
        Basically mimicks "Set Pressure" button on UniStream HMI.

        :param sp: the setpoint pressure.
        '''
        self.plc.write_float(self.ad['Setpoint pressure'], sp)
        self.plc.write_coil(self.ad['submit_setpoint'], value=True)
        time.sleep(1.0) # Wait for the submit_setpoint bit to adjust <--yay this fixed it!
        self.plc.write_coil(self.ad['submit_setpoint'], value=False)

    def _check_autotune(self):
        autotune_complete = self.plc.read_coil(self.ad['PID Configuration.Autotune Done'])
        if autotune_complete:
            return
        else:
            print('[STATUS] No autotune parameters found.')
            self._autotune()

    def _autotune(self):
        '''
        Completes an autotune sequence at the current setpoint.
        This function assumes that a setpoint has already been set by toggling
        the submit_setpoint bit.

        :return: False for failure and True for success
        '''
        print('[STATUS] Autotuning...')
        self.plc.write_coil(self.ad['run_autotune'], value=True)
        
        timeout = time.time() + 600 # 10 min timeout--should be enough but if the autotune isn't finishing by then I can change

        autotune_complete = False
        while not autotune_complete:
            if time.time() > timeout:
                raise RuntimeError('Autotune timeout')
            autotune_complete = self.plc.read_coil(self.ad['PID Configuration.Autotune Done'])
            time.sleep(1.0)
        print('[STATUS] Autotune complete.')

    def _set_pressure(self, sp, max_err):
        '''
        :return: True for successful settling, False for timeout.
        '''
        print(f'[STATUS] Adjusting pressure to setpoint ({sp} {self.unit})...')
        self.plc.write_coil(self.ad['run_PID'], value=True)

        # Establish a max time in case setpoint is unreachable
        sp_timeout = False
        setpoint_timeout = self.config.get_default('setpoint_timeout')
        timeout = time.time() + setpoint_timeout # 10 minute timeout rn

        # Wait for the setpoint to settle.
        setpoint_settle = self.config.get_default('setpoint_settle') # how long the setpoint must be stable to begin data collection.
        settle_start = None
        while True:
            # Check for timeout
            if time.time() > timeout:
                print(f'[WARNING] Setpoint is unreachable after {setpoint_timeout}s')
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
                    print(f'[STATUS] Settled. Collecting data for setpoint ({sp} {self.unit})...')
                    return True
            else:
                # reset timer if tolerance band is exceeded.
                settle_start = None

            time.sleep(0.01) # a 100Hz sample rate seemed to work alright for settling time.

    def _record_data(self, times, cal, uut):
        '''
        Once a setpoint is reached, samples data from the MKS 1 sensor on the cart
        as well as the unit under test at a regular sampling rate, for a designated
        amount of time.

        :param times: An existing list of times corresponding to sample points from previous setpoints. This function appends new times.
        :param cal: The existing list of sample points from previous setpoints for the MKS 1 sensor.
        :param uut: The existing list of sample points from previous setpoints for the unit under test.
        :return times: The same as the input but appended with new sample point times.
        :return cal: The same as the input but appended with new sample point pressures.
        :return uut: The same as the input but appended with new sample point pressures.
        '''
        # Check settings for how long to record and sampling rate
        setpoint_wait = self.config.get_default('setpoint_wait')
        sample_rate = self.config.get_default('sample_rate')

        record_start = time.time()
        while time.time() - record_start < setpoint_wait:
            # Collect data from MKS 1 sensor
            cal_value = self.plc.read_float(self.ad['MKS 1 pressure'])
            uut_value = self.plc.read_float(self.ad['UUT pressure'])
            times.append(time.time())
            cal.append(cal_value)
            uut.append(uut_value)
            # Wait
            time.sleep(1.0 / sample_rate)
        return times, cal, uut