#gui/gui.py 
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import threading
from calibration.calibration import CalibrationSequence
from utils.constants import ADDRESSES, UNITS
import pandas as pd
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
            are also stored as local attributes. Many of them are stored in the _widget_dict attribute, a 
            dicitonary with all of the config INI options stored as StringVars.

        - Make a dictionary of available user-entered commands.
        '''

        # Initialize things
        # ~~~~~~~~~~~~~~~~~

        super().__init__() # Initialize the parent class (Tkinter root window)

        # Setup gui window
        self.title("CalCart 2025 IMA Life North America")
        self.iconbitmap("./gui/logo.ico")
        self.protocol("WM_DELETE_WINDOW", self._cmd_shutdown)

        # Initialize object references
        self.plc = plc # stateful reference to variable `plc` in main
        self.config = config # stateful reference to variable `config` in main
        
        # Initialize the config INI path as a StringVar
        self._configpath = tk.StringVar(value='<--- Select a configuration.')

        # Initialize the "save results directory" path as a StringVar
        self._resultspath = tk.StringVar(value="<--- Choose where to save calibration data.")

        # Initialize the _widget_dict attribute
        self._get_config_dict()

        # Initialize an indicator for if a calibration is being made.
        self.is_busy = False

        # Initialize the status variable (currently not used)
        self._statusvar = tk.StringVar(value='Status: waiting for action...')

        
        # Set up basic window and layout
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            # Main/Parent Frame
            # ~~~~~~~~~~~~~~~~~
        pfrm = ttk.Frame(self, padding='10')
        pfrm.pack(fill='both', expand=True)
        pfrm.columnconfigure(0, weight=0)  # general options column stays fixed
        pfrm.columnconfigure(1, weight=0)  # setpoint settings column stays fixed
        pfrm.rowconfigure(1, weight=1)

            # Subframes
            # ~~~~~~~~~
            
        # --File--
        # (Top left/middle)
        filefrm = ttk.LabelFrame(pfrm, text='File', padding='10')
        filefrm.grid(column=0, row=0, columnspan=2, sticky="ew")
        filefrm.columnconfigure(1, weight=1)
        filefrm.grid_propagate(False)
        filefrm.configure(width=800, height=120)
        self._set_filefrm(filefrm)

        # --General Settings--
        # (Bottom left)
        self._stngfrm = ttk.LabelFrame(pfrm, text="Calibration Sequence Options", padding='10')
        self._stngfrm.grid(column=0, row=1, sticky="nsew")
        self._stngfrm.columnconfigure(1, weight=1)
        self._stngfrm.grid_propagate(False)
        self._stngfrm.configure(width=400, height=300)
        self._set_stngfrm(self._stngfrm)

        # --Setpoint Settings--
        # (Bottom right)
        self._spfrm = ttk.LabelFrame(pfrm, text="Setpoints", padding='10')
        self._spfrm.grid(column=1, row=1, sticky='nsew')
        self._spfrm.columnconfigure(1, weight=1)
        self._spfrm.grid_propagate(False)
        self._spfrm.configure(width=400, height=300)
        self._set_spfrm(self._spfrm)

        # --Calibration Run Frame--
        # (Far top right)
        runfrm = ttk.Frame(pfrm, padding='10')
        runfrm.grid(column=2, row=0, sticky='nsew')
        self._set_runfrm(runfrm)

        # --Console Frame--
        # (Far bottom right)
        confrm = ttk.LabelFrame(pfrm, text='Console', padding='10')
        confrm.grid(column=2, row=1, sticky='ns')
        self._set_confrm(confrm)


        # Command dictionary
        # ~~~~~~~~~~~~~~~~~~

        self._commands = {
            'help': self._cmd_help,
            'status': self._cmd_status,
            'stop': self._cmd_shutdown,
            'cls': self._cmd_clear,
            'echo': self._cmd_echo,
            'busy': self._cmd_make_busy,
            'bypass': self._cmd_bypass,
            'connect': self._cmd_connect,
            'report': self._cmd_report,
            'apply': self._set_config_dict,
        }
     
    # -----------------------------------------------------------------------------------------------------


    # Create/refresh subframes
    # ~~~~~~~~~~~~~~~~~~~~~~~~

    def _set_filefrm(self, filefrm):
        '''
        Same thing for the file frame
        '''
        # Load config button
        ttk.Button(filefrm, text='Load Configuration', command=self._load_config, width='20').grid(column=0, row=0)
        ttk.Label(filefrm, textvariable=self._configpath, anchor="w").grid(column=1, row=0, sticky="ew")

        # Save data button
        ttk.Button(filefrm, text='Results Directory', command=self._choose_resultspath, width='20').grid(column=0, row=1)
        ttk.Label(filefrm, textvariable=self._resultspath, anchor="w").grid(column=1, row=1, sticky="ew")

        # Save buttons
        ttk.Button(filefrm, text='Apply Changes', command=self._set_config_dict).grid(column=0, row=2, sticky='w')
        ttk.Button(filefrm, text='Save Configuration', command=self._save_config).grid(column=1, row=2, sticky='w')

    def _set_stngfrm(self, frm):
        '''
        Sets up all the widgets for user settings in the [general], [customer], [device_info], 
        and [standard_info] sections of the config. Binds the StringVars to the widgets. This 
        must be redone if the config dictionary is recreated.
        '''
        self._clear_frame(frm)

        # --General--

        d = self._widget_dict['general']

        # Section title
        ttk.Label(
            frm, text='General Settings', font=('TkDefaultFont', 10, 'bold')
        ).pack(fill='x', pady=(0, 5))

        # Setpoint wait
        self._setting(frm, 'Setpoint wait time [s]: ', 'general', 'setpoint_wait')

        # Sample rate
        self._setting(frm, 'Sample rate [Hz]: ', 'general', 'sample_rate')

        # Setpoint settle
        self._setting(frm, 'Setpoint settling time [s]: ', 'general', 'setpoint_settle')

        # Setpoint timeout
        self._setting(frm, 'Setpoint timeout [s]: ', 'general', 'setpoint_timeout')

        # Number of setpoints
        self._setting(frm, 'Number of setpoints: ', 'general', 'num_setpoints')

        # Autotune each setpoint
        row = ttk.Frame(frm)
        row.pack(fill='x', pady=2)
        ttk.Label(
            row, text='Autotune each setpoint? ', width=24, anchor='e'
        ).pack(side='left')
        ttk.Checkbutton(
            row, variable=d['autotune_each'], offvalue='no', onvalue='yes'
        ).pack(side='left', fill='x', expand=True)

        # Units
        row = ttk.Frame(frm)
        row.pack(fill='x', pady=2)
        ttk.Label(
            row, text='Pressure units: ', width=24, anchor='e'
        ).pack(side='left')
        ttk.Combobox(
            row, 
            textvariable=d['unit'], 
            values=list(UNITS.values()), 
            state='readonly'
        ).pack(side='left', fill='x', expand=True)

        btnrow = ttk.Frame(frm)
        btnrow.pack(fill='x', pady=2)
        ttk.Button(
            btnrow, text='Apply Units', command=self._set_unit
        ).pack(fill='x', pady=(5, 0))

        # --Customer--

        d = self._widget_dict['report']

        # Section title
        ttk.Label(
            frm, text='Customer Information', font=('TkDefaultFont', 10, 'bold')
        ).pack(fill='x', pady=(0, 5))

        # Company name
        self._setting(frm, 'Company Name: ', 'report', 'company')

        # Project name
        self._setting(frm, 'Project Name: ', 'report', 'project')

        # Service number
        self._setting(frm, 'Service Number: ', 'report', 'service_number')

        # Machine name
        self._setting(frm, 'Machine Name: ', 'report', 'machine')

        # Location
        self._setting(frm, 'Location: ', 'report', 'location')

        # Date
        self._setting(frm, 'Date: ', 'report', 'date')

        # Calibration type
        self._setting(frm, 'Calibration Type: ', 'report', 'calibration_type')

        # Procedure
        self._setting(frm, 'Procedure: ', 'report', 'procedure')

        # Calibration
        self._setting(frm, 'Calibration: ', 'report', 'calibration')

    def _set_spfrm(self, frm):
        '''
        In the future, I will make the `self._spfrm` frame into a canvas, in order to add scrolling if too many 
        setpoints are added to display at once on the screen.
        '''
        self._clear_frame(frm)
  
        num_setpoints = self.config.getg('num_setpoints', cast=int)

        for i in range(num_setpoints):

            # Section title
            ttk.Label(
                frm, text=f'Setpoint {i+1}', font=('TkDefaultFont', 10, 'bold')
            ).pack(fill='x', pady=(0, 5))

            # Setpoint pressure
            self._setting(
                frm,
                f'Setpoint pressure [{self.config.getg("unit", cast=str)}]: ',
                f'setpoint.{i+1}',
                'pressure',
                extra_wide=True
            )

            # Setpoint error tolerance
            self._setting(
                frm,
                f'Setpoint error tolerance [{self.config.getg("unit", cast=str)}]: ',
                f'setpoint.{i+1}',
                'max_err',
                extra_wide=True
            )

    def _set_runfrm(self, frm):
        '''
        Instantiates the _progressbar local attribute which can be 
        started/stopped to indicate that a calibration sequence is in progress. 
        '''
        ttk.Button(
            frm, text='Run\nCalibration\nSequence', command=self._cal
        ).grid(column=0, row=0, rowspan=2, padx=10, sticky='ns')

        ttk.Label(frm, textvariable=self._statusvar).grid(column=1, row=0)
        self._progressbar = ttk.Progressbar(frm, orient='horizontal', mode='indeterminate', length=350)
        self._progressbar.grid(column=1, row=1, pady=5, padx=10)

    def _set_confrm(self, frm):
        '''
        Instantiates the local attributes _console and _entry to be 
        used when handling/displaying command entries.
        '''
        self._console = ScrolledText(frm, font=('Consolas', 11), height=12)
        self._console.pack(fill='both', expand=True)
        self._console.insert(tk.END, 'Application started.\n')
        self._console.config(state='disabled') # Stop the user from writing in the console window.

        entrybox = tk.Frame(frm)
        entrybox.pack(fill='x')

        tk.Label(entrybox, text='>', font=('Consolas', 11)).pack(side='left', padx=(5,2))
        self._entry = tk.Entry(entrybox, font=('Consolas', 11))
        self._entry.pack(side='left', fill='x', expand=True, padx=(0,5))
        self._entry.bind("<Return>", self._execute)

    def _setting(self, frm, setting_name, ini_section, ini_key, extra_wide=False):
        '''
        To be used in the above methods. Creates and packs a new setting to the table.
        Only used for generic string entry type settings. The rest you gotta do yourself.
        '''
        if extra_wide:
            w = 34
        else:
            w = 24
        row = ttk.Frame(frm)
        row.pack(fill='x', pady=2)
        ttk.Label(
            row, text=setting_name, width=w, anchor='e'
        ).pack(side='left')
        ttk.Entry(
            row, textvariable=self._widget_dict[ini_section][ini_key]
        ).pack(side='left', fill='x', expand=True)

    def _clear_frame(self, frm):
        for child in frm.winfo_children():
            child.destroy()

    # --------------------------------------------------------------------------------------------------------------------------------


    # load/apply/retrieve/edit configuration settings
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _set_unit(self):
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
        new_unit = self._widget_dict['general']['unit'].get()

        # Apply any other changes the user has made since last applying changes. 
        # This is done so that the unit change is applied to the most recent values 
        # of the setpoints, not the last saved values.
        self._set_config_dict()

        # Convert the newly applied values according to the new unit.
        # Nothing's stopping the .units method from working if the current
        # unit in the config is the same as the new unit (it still works to convert
        # the pressure values)
        self.config.units(new_unit, old_unit=old_unit)

        # Retrieve the newly converted values and update the GUI to match.
        self._get_config_dict() # Refresh the widget dictionary to match the new config.
        self._set_stngfrm(self._stngfrm) # Refresh the general settings frame to match the new config.
        self._set_spfrm(self._spfrm) # Refresh the setpoint settings frame to match the new config.

        # Set the units on the PLC.
        self.plc.set_units(new_unit)

    def _get_config_dict(self):
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
        self._widget_dict = widget_dict

    def _set_config_dict(self, args=None):
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
        widget_dict = self._widget_dict
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
        self._get_config_dict()
        # Refresh the settings windows
        self._set_stngfrm(self._stngfrm)
        self._set_spfrm(self._spfrm)

        # Set the units on the PLC.
        if self.plc.connected:
            self.plc.set_units(self.config.getg('unit', cast=str))

    def _load_config(self):
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
            self._configpath.set(load_path)
            # reset the settings dictionaries using the new config
            self._get_config_dict()
            # Refresh the settings windows
            self._set_stngfrm(self._stngfrm)
            self._set_spfrm(self._spfrm)

            # Set the units on the PLC
            self.plc.set_units(self.config.getg('unit', cast=str))
            
        else: # Don't do anything if the user picks a bad path
            return

    def _save_config(self):
        '''
        Saves a config that has been edited in the GUI.
        '''
        # Apply changes
        self._set_config_dict()
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
            self._configpath.set(save_path)
            self.log('[STATUS] Configuration saved.')

    # -----------------------------------------------------------------------------------------------------------------------


    # Calibration sequence
    # ~~~~~~~~~~~~~~~~~~~~

    def _choose_resultspath(self):
            save_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes = [("comma-separated value file", "*.csv"), ("Excel file", "*.xlsx")]
            )
            self._resultspath.set(save_path)
    
    def _cal(self):
        '''
        Opens up a worker thread which performs a calibration sequence.
        When the calibration sequence is finished, activates callback function.

        *For now I will assume the save path is valid; eventually I will add a popup warning if it is not.
        '''
        def callback():
            self.is_busy = False
            self._progressbar.stop()
            self.log(f'[STATUS] Calibration data saved to {self._resultspath.get()}')

        def worker():
            try:
                cal_seq = CalibrationSequence(
                    self.plc,
                    self.config,
                    self._widget_dict['general']['unit'].get(),
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
        
        save_path = self._resultspath.get()
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
        self._progressbar.start()
        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def _save_results(self, results):
        '''
        Saves the results.
        '''
        save_path = self._resultspath.get()

        if save_path.endswith(".csv"):
            results.to_csv(save_path, index=False)
        elif save_path.endswith(".xlsx"):
            results.to_excel(save_path, index=False)

    # -------------------------------------------------------------------------------------------------------------------------


    # Embedded cli commands
    # ~~~~~~~~~~~~~~~~~~~~~
    
    def log(self, msg):
        '''
        Sends a message to the console window.
        '''
        self._console.config(state='normal')
        self._console.insert(tk.END, str(msg)+'\n')
        self._console.see(tk.END)
        self._console.config(state='disabled')

    def log_from_thread(self, msg):
        '''
        Safely logs messages from worker threads by scheduling them on the Tk main thread.
        '''
        self.after(0, lambda: self.log(str(msg)))

    def _execute(self, event=None):
        raw = self._entry.get()
        if not raw:
            return
        self._entry.delete(0, tk.END)

        command, *args = raw.split(' ')

        self.log(f'>{raw}')

        cmd_func = self._commands.get(command)
        if cmd_func:
            cmd_func(args)
        else:
            self.log('[WARNING] Unknown command.')

    def _cmd_shutdown(self, args=None):
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
    
    def _cmd_clear(self, args=None):
        '''
        Clears the console window.
        '''
        self._console.config(state='normal')
        self._console.delete('1.0', tk.END)
        self._console.config(state='disabled')

    def _cmd_status(self, args=None):
        '''
        Shows active pressure units.
        Reads pressure sensor input registers.
        '''
        if self.plc.connected:
            self.log(f'System using pressure units: {self.config.getg('unit', cast=str)}')
            transducers = ['MKS 1 pressure', 'MKS 2 pressure', 'MKS 3 pressure']
            for t in transducers:
                value = self.plc.read_float(ADDRESSES[t])
                self.log(f'{t}: {value:.2f} {self.config.getg('unit', cast=str)}')
        else:
            self.log('Offline.')

    def _cmd_bypass(self, args=None):
        '''
        Bypasses the startup sequence in UniLogic.
        '''
        if self.plc.connected:
            self.plc.write_coil(ADDRESSES['bypass_startup'], value=True)

    def _cmd_help(self, args=None):
        '''
        Lists available commands in the embedded CLI.
        '''
        self.log('Available commands:')
        for cmd in self._commands.keys():
            self.log(f'  {cmd}')

    def _cmd_echo(self, args):
        '''
        Echoes the input arguments back to the console.
        '''
        self.log(' '.join(args))

    def _cmd_make_busy(self, args=None):
        '''
        For testing purposes
        '''
        if self.is_busy:
            self.is_busy = False
        else:
            self.is_busy = True

    def _cmd_connect(self, args=None):
        '''
        Connect to PLC
        '''
        try:
            self.plc.connect()
            unit = self.plc.get_units()
            self.log(f'Connected to PLC.')
            self.log(f'System using pressure units: {unit}')
        except Exception as e:
            self.log(f'Error: {e}. Check PLC IP address and network connection.')

    def _cmd_report(self, args):
        '''
        Saves a report with artificial setpoint data.

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