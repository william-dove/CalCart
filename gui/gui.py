#gui/gui.py 

# Local
from gui.frames import (
    FileFrame,
    GeneralSettingsFrame,
    SetpointSettingsFrame,
    CalibrationRunFrame,
)
from gui.cli import ConsoleFrame
from calibration.calibration import CalibrationSequence
from utils.constants import ADDRESSES

# Other
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

import threading
import os


class GUI(tk.Tk):
    '''
    A derived class from the tk.Tk class which acts as a gui to interface
    with the program.

    __init__ parameters:
    :param plc: [class Slave] Must be initialized in main prior to initializing this class.
    :param config: [class ConfigLoader] See above^.
    :param addresses: Dictionary of modbus addresses for convenient reference.
    :param unit: Actively used pressure unit (FUTURE: make changeable from gui/cli)
    '''
    def __init__(self, plc, config):
        '''
        - Initialize Tkinter root, reference attributes and local attributes
            ("reference" attributes don't have a leading underscore, and are assigned to input
            parameters which are instances of other classes initialized in main.py)
            ("local" attributes are given a leading underscore, and represent variables only
            used within the class)

        - Set up the basic window format. The parent frame (`pfrm`) lives within the `tk.Tk` window 
            and other subframes (for different user I/O) are children of this frame. Frames
            that remain static after being formed are just instantiated within the __init__ method,
            but frames like the user settings or command console need to be refreshed are stored as local
            attributes.
        
        - Add ttk I/O elements to the subwindows defined above. Each text element (e.g., input entry boxes
            or dynamic text labels) is linked to a tkinter `tk.StringVar` object. These StringVar objects 
            are also stored as local attributes. Many of them are stored in the widget_dict attribute, a 
            dicitonary with all of the config INI options stored as StringVars.

        - Make a dictionary of available user-entered commands.
        '''

        # Setup the window and important attributes
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        super().__init__() # Initialize the parent class (Tkinter root window)

        self.title("CalCart 2025 IMA Life North America")
        self.iconbitmap("./gui/logo.ico")
        self.protocol("WM_DELETE_WINDOW", self.shutdown)

        # Initialize object references
        self.plc = plc # stateful reference to variable `plc` in main
        self.config = config # stateful reference to variable `config` in main
        
        # Initialize attributes
        self.configpath = tk.StringVar(value='<--- Select a configuration.')
        self.resultspath = tk.StringVar(value="<--- Choose where to save calibration data.")
        self.statusvar = tk.StringVar(value='Status: waiting for action...') # Displays current activities
        self.is_busy = False # Indicator on when a calibration is being made

        # Initialize the widget_dict attribute based on `self.config`
        self.config_to_widgets()

        
        # Set up basic frame/subframe layout
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # Main/Parent Frame
        self.frame = ttk.Frame(self, padding='10')
        self.frame.pack(fill='both', expand=True)
        self.frame.columnconfigure(0, weight=0)  # general options column stays fixed
        self.frame.columnconfigure(1, weight=0)  # setpoint settings column stays fixed
        self.frame.rowconfigure(1, weight=1)

        # Subframes (`frames.py` and `cli.py`)
        self.subframes = {
            'file': FileFrame(self),
            'general': GeneralSettingsFrame(self),
            'setpoints': SetpointSettingsFrame(self),
            'calibration': CalibrationRunFrame(self),
            'console': ConsoleFrame(self)
        }

    # --------------------------------------------------------------------------------------------------------------------------------


    # Configuration
    # ~~~~~~~~~~~~~

    def config_to_widgets(self):
        '''
        Copies the config dict to a dict made up of stringvars.

        config_dict is a nested dict of strings.
        widget_dict is a nested dict of tk.StringVars
        self._cd is the attribute of this class containing the 
        widget_dict.
        '''
        config_dict = self.config.get_dict()
        widget_dict = {}
        for section in config_dict:
            widget_dict[section] = {
                setting: tk.StringVar(value=val)
                for setting, val in config_dict[section].items()
            }
        self.widget_dict = widget_dict

    def widgets_to_config(self, args=None):
        '''
        Activates when the "Apply Changes" button is pressed.
        Takes the widget dict attribute of the gui class, which may have been edited
        by the user. Copies this dict back to a normal string dict and sends this to
        the config using the `.set_dict` method.

        * In order to change setpoint settings, the user must first change the "Number of setpoints" setting 
            in the general settings, apply changes to refresh the setpoint settings window, and then edit the
            setpoint settings and click apply changes a second time.

        * When the user increases the number of setpoints and applies the change, the additional sections in
            the INI are created with the same values as `[setpoint.1]`.

        **This docstring may not be up-to-date but I'm too lazy to rewrite it.
        '''
        widget_dict = self.widget_dict
        config_dict = {}
        for section in widget_dict:
            config_dict[section] = {
                key: val.get()
                for key, val in widget_dict[section].items()
            }
        # Ensure at least one setpoint has been added.
        num_setpoints = int(config_dict['general']['num_setpoints'])
        if num_setpoints < 1:
            config_dict['general']['num_setpoints'] = '1'
        # Add sections for new setpoints, if number of setpoints has been changed.
        for i in range(num_setpoints):
            if f'setpoint.{i+1}' in config_dict:
                continue
            else:
                config_dict[f'setpoint.{i+1}'] = config_dict['setpoint.1']
        # Apply the new dictionary to the config
        self.config.set_dict(config_dict)
        # Reset the widget dictionary using these new values
        self.config_to_widgets()
        # Refresh the settings windows
        self._refresh_widgets()

        # Set the units on the PLC.
        if self.plc.connected:
            self.plc.set_units(self.config.getg('unit', cast=str))

    def set_unit(self):
        '''
        Updates the configuration to match the user-inputted unit.
        If the user clicks "Apply Units" in the GUI, this function is called. 
        It updates the config to match the new unit, and also converts all 
        setpoint pressures and tolerances to the new units.

        If the user instead clicks "Apply Changes" at the top, the unit will be changed,
        but all values are assumed to be in the new units, and no conversion is done. 
        This is because the user may have manually changed the setpoint values to match 
        the new units, and we don't want to convert them again.
        '''
        # Stow the old unit before applying all changes (this way it's remembered for the conversion after).
        old_unit = self.config.getg('unit', cast=str)

        # Stow the new unit (which will be applied to the config after this)
        new_unit = self.widget_dict['general']['unit'].get()

        # Apply any other changes the user has made since last applying changes. 
        # This is done so that the unit change is applied to the most recent values 
        # of the setpoints, not the last saved values.
        self.widgets_to_config()

        # Convert the newly applied values according to the new unit.
        # Nothing's stopping the .units method from working if the current
        # unit in the config is the same as the new unit (it still works to convert
        # the pressure values)
        self.config.units(new_unit, old_unit=old_unit)

        # Retrieve the newly converted values and update the GUI to match.
        self.config_to_widgets() # Refresh the widget dictionary to match the new config.
        self._refresh_widgets()

        # Set the units on the PLC.
        self.plc.set_units(new_unit)

    def load_config(self):
        '''
        Activates when the "Load Configuration" button is pressed. 
        Loads an existing configuration. This can also be done when executing the program (see main.py)

        * Changing self.config SHOULD mutate the `config = ConfigLoader()` object initialized in `main.py`
            ...but who knows. At any rate I'll just use this class attribute when running a calibration sequence
            or changing config parameters.

        * I made it so the whole general settings frame (`self._genfrm`) is refreshed when a new config is loaded,
            so I can just re-initialize the general dictionary of StringVars and tie the new ones to the new frame
            widgets.
        '''
        load_path = filedialog.askopenfilename(
            defaultextension='.ini',
            filetypes=[("INI file", "*.ini")]
        )
        if load_path.endswith('.ini'):
            self.config.load(load_path) # Error handling done here
            self.log(f'[STATUS] Opened configuration file {load_path}')
            self.configpath.set(load_path)
            # reset the settings dictionaries using the new config
            self.config_to_widgets()
            # Refresh the settings windows
            self._refresh_widgets()

            # Set the units on the PLC
            self.plc.set_units(self.config.getg('unit', cast=str))
            
        else: # Don't do anything if the user picks a bad path
            return

    def save_config(self):
        '''
        Saves a config that has been edited in the GUI.
        '''
        # Apply changes
        self.widgets_to_config()
        # Save the configuration
        save_path = filedialog.asksaveasfilename(
            defaultextension='.ini',
            filetypes=[("INI file", "*.ini")]
        )
        if not save_path:
            self.log('[STATUS] Save cancelled.')
        elif not save_path.endswith('.ini'):
            self.log('[WARNING] Configuration file not saved as .ini. Cancelling...')
        else:
            self.config.save(save_path)
            self.configpath.set(save_path)
            self.log('[STATUS] Configuration saved.')

    def _refresh_widgets(self):
        '''
        Re-creates the settings subframes to match a new config.
        Also re-ties each entry widget to its StringVar.
        '''
        self.subframes['general'].refresh()
        self.subframes['setpoints'].refresh()

    # -----------------------------------------------------------------------------------------------------------------------


    # Calibration sequence
    # ~~~~~~~~~~~~~~~~~~~~

    def choose_resultspath(self):
            save_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes = [("comma-separated value file", "*.csv"), ("Excel file", "*.xlsx")]
            )
            self.resultspath.set(save_path)
    
    def cal(self):
        '''
        Opens up a worker thread which performs a calibration sequence.
        When the calibration sequence is finished, activates callback function.

        *For now I will assume the save path is valid; eventually I will add a popup warning if it is not.
        '''
        def callback():
            self.is_busy = False
            self.subframes['calibration'].stop_anim()
            self.log(f'[STATUS] Calibration data saved to {self.resultspath.get()}')

        def worker():
            try:
                cal_seq = CalibrationSequence(
                    self.plc,
                    self.config,
                    self.widget_dict['general']['unit'].get(),
                    self.log_from_thread
                )

                results = cal_seq.run()

                self._save_results(results)

            except Exception as e:
                self.log_from_thread(f"[ERROR] {e}")

            finally: 
                # When the worker is finished (i.e. calibration sequence complete), the
                # built-in `.after` method of the Tk class will call this function in the
                # main thread immediately/as soon as the main thread is available ("after
                # 0 seconds")
                self.after(0, callback)

        # Only proceed if ready:
        if not self.plc.connected:
            self.log('[WARNING] PLC connection failed. Check PLC IP address and network connection.')
            return
        
        if self.is_busy:
            self.log('[STATUS] Calibration already in progress.')
            return
        
        save_path = self.resultspath.get()
        save_dir, save_filename = os.path.split(save_path)
        save_dir = save_dir or '.' # If the directory is the current directory.

        if not save_path or save_path.startswith("<---"):
            self.log('[WARNING] No save path selected.')
            return
        
        if not save_filename.endswith(('.csv', '.xlsx')):
            self.log('[WARNING] Invalid save file format. Please select a .csv or .xlsx file.')
            return
        
        if not os.path.isdir(save_dir):
            self.log('[WARNING] Invalid save directory.')
            return

        # Start the calibration
        self.is_busy = True
        self.subframes['calibration'].start_anim()
        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def _save_results(self, results):
        '''
        Saves the results.
        '''
        save_path = self.resultspath.get()

        if save_path.endswith(".csv"):
            results.to_csv(save_path, index=False)
        elif save_path.endswith(".xlsx"):
            results.to_excel(save_path, index=False)

    # -------------------------------------------------------------------------------------------------------------------------


    # Commands and utility
    # ~~~~~~~~~~~~~~~~~~~~
    
    def log(self, msg):
        '''
        Logs to the console.
        '''
        self.subframes['console'].log(msg)

    def log_from_thread(self, msg):
        '''
        Safely logs messages from worker threads by scheduling them on the Tk main thread.
        '''
        self.after(0, lambda: self.log(str(msg)))

    def shutdown(self, args=None):
        '''
        Safely closes the program. Activated either by the red X in the GUI
        or the `stop` command in the CLI.

        * I'm not sure how the `stop` command will function now that CLI commands are 
        being executed on a separate thread. Maybe it will still work?
        '''
        if args and args[0] == 'hard':
            self.log('[STATUS] Aborting...')
        elif self.is_busy:
            self.log('[WARNING] Calibration in progress. Please wait for it to finish before closing the program.')
            return
        else:
            self.log('[STATUS] Exiting...')

        self.plc.close()
        self.quit()
        self.destroy()

    def status(self, args=None):
        '''
        Shows active pressure units.
        Reads pressure sensor input registers.

        command: status
        '''
        if self.plc.connected:
            self.log(f'System using pressure units: {self.config.getg('unit', cast=str)}')
            transducers = ['MKS 1 pressure', 'MKS 2 pressure', 'MKS 3 pressure']
            for t in transducers:
                value = self.plc.read_float(ADDRESSES[t])
                self.log(f'{t}: {value:.2f} {self.config.getg('unit', cast=str)}')
        else:
            self.log('Offline.')

    def bypass(self, args=None):
        '''
        Bypasses the startup sequence in UniLogic.

        command: bypass
        '''
        if self.plc.connected:
            self.plc.write_coil(ADDRESSES['bypass_startup'], value=True)


    def make_busy(self, args=None):
        '''
        For testing purposes

        command: make_busy
        '''
        if self.is_busy:
            self.is_busy = False
        else:
            self.is_busy = True

    def connect(self, args=None):
        '''
        Connect to PLC

        command: connect
        '''
        try:
            self.plc.connect()
            unit = self.plc.get_units()
            self.log(f'Connected to PLC.')
            self.log(f'System using pressure units: {unit}')
        except Exception as e:
            self.log(f'Error: {e}. Check PLC IP address and network connection.')

    def report(self, args):
        '''
        Saves a report with artificial setpoint data.

        command: report

        :args[0]: path to save results at.
        '''
        try:
            fake = CalibrationSequence(
                self.plc,
                self.config,
                self.log
            )
            fake.generate_report(args[0])

        except Exception as e:
            self.log(f'[ERROR] {e}.')

        finally:
            self.log('Report saved.')