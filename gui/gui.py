#gui/gui.py 
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import threading
from calibration.calibration import CalibrationSequence
from utils.constants import ADDRESSES, UNITS
import sys
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

        - Set up the basic window format. The parent window (`frm`) is a child of the Tkinter root 
            (this class) and the parent of other subwindows for different user I/O.
        
        - Add GUI I/O elements to the subwindows defined above. The I/O objects are linked to Tkinter 
            StringVar objects, which are stored in a local attribute dictionaries `self_dcondif` and `self._spconfigs`. 
            The dictionary keys match those of the settings in the INI configuration file.  
            The `._initddict()` and `._initspdicts()` methods are used to read the values for each setting in a loaded
            INI configuration file, and set the local dictionary of StringVars to match.
            The `._setddict()` and `._setspdicts()` methods write back the edited StringVar values to the config, which
            is then saved as a new configuration file.
        '''

        # Initialize things
        # ~~~~~~~~~~~~~~~~~

        super().__init__() # Initialize the parent class (Tkinter root)

        # Setup gui window
        self.title("CalCart 2025 IMA Life North America")
        self.iconbitmap("./gui/logo.ico")
        self.protocol("WM_DELETE_WINDOW", self._cmd_shutdown)

        # Initialize object references
        self.plc = plc # stateful reference to variable `plc` in main
        self.config = config # stateful reference to variable `config` in main
        
        # Get the INI path as a StringVar
        if self.config.path is not None: # i.e. if the user loaded a config path on startup
            self._configpath = tk.StringVar(value=self.config.path) 
        else: # If the user did not load a config path, use the defualt config settings and prompt the user to select a config file.
            self._configpath = tk.StringVar(value='<--- Select a configuration.')

        # Initialize the "save results directory" tkinter variable
        self._resultspath = tk.StringVar(value="<--- Choose where to save calibration data.")

        # Initialize the widget setting dictionary
        self._get_config_dict()

        # Make indicator to block the cli from input
        self.is_busy = False

        # Initialize the status variable
        self._statusvar = tk.StringVar(value='Status: waiting for action...')

        # Initialize command dicitonary
        self._commands = {
            'help': self._cmd_help,
            'status': self._cmd_status,
            'stop': self._cmd_shutdown,
            'cls': self._cmd_clear,
            'echo': self._cmd_echo,
            'busy': self._cmd_make_busy,
            'bypass': self._cmd_bypass
        }

        # ---------------------------------------------------------------------------------------------

        # Set up basic window and layout
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # --Main/Parent Frame--
        frm = ttk.Frame(self, padding='10')
        frm.pack(fill='both', expand=True)
        frm.columnconfigure(0, weight=0)  # left side stays fixed
        frm.columnconfigure(1, weight=1)  # right side expands
        frm.rowconfigure(1, weight=1)


        # --Subframes--
            # Only the subframes which are *dynamic*, i.e. edited or
            # refreshed after the gui is initialized in main, are stored 
            # as local attributes. The other ones are just local variables
            # inside of the __init__ function.
        # File subframe (Top left/middle)
        filefrm = ttk.LabelFrame(frm, text='File', padding='10')
        filefrm.grid(column=0, row=0, columnspan=2, sticky="ew")
        filefrm.columnconfigure(1, weight=1)
        filefrm.grid_propagate(False)
        filefrm.configure(width=800, height=120)

        # General [DEFAULT] settings subframe (Bottom left)
        self._genfrm = ttk.LabelFrame(frm, text="Calibration Sequence Options", padding='10')
        self._genfrm.grid(column=0, row=1, sticky="nsew")
        self._genfrm.columnconfigure(1, weight=1)
        self._genfrm.grid_propagate(False)
        self._genfrm.configure(width=400, height=300)

        # Setpoint settings subframe (Bottom right)
        self._spfrm = ttk.LabelFrame(frm, text="Setpoints", padding='10')
        self._spfrm.grid(column=1, row=1, sticky='nsew')
        self._spfrm.columnconfigure(1, weight=1)
        self._spfrm.grid_propagate(False)
        self._spfrm.configure(width=400, height=300)

        # Calibration subframe (Far top right)
        calfrm = ttk.Frame(frm, padding='10')
        calfrm.grid(column=2, row=0, sticky='nsew')

        # Console (Far bottom right)
        confrm = ttk.LabelFrame(frm, text='Console', padding='10')
        confrm.grid(column=2, row=1, sticky='ns')
        # ------------------------------------------------------------------------

        # Add GUI elements
        # ~~~~~~~~~~~~~~~~

        # --File--
        self._set_filefrm(filefrm)

        # --Settings--
        self._set_genfrm()

        # --Setpoint Settings--
        self._set_spfrm()

        # --Calibration Run Frame--
        ttk.Button(
            calfrm, text='Run\nCalibration\nSequence', command=self._cal
        ).grid(column=0, row=0, rowspan=2, padx=10, sticky='ns')

        ttk.Label(calfrm, textvariable=self._statusvar).grid(column=1, row=0)
        self._progressbar = ttk.Progressbar(calfrm, orient='horizontal', mode='indeterminate', length=350)
        self._progressbar.grid(column=1, row=1, pady=5, padx=10)

        # --Console Frame--
        self._console = ScrolledText(confrm, font=('Consolas', 11), height=12)
        self._console.pack(fill='both', expand=True)
        self._console.insert(tk.END, 'Application started.\n')
        self._console.config(state='disabled') # Stop the user from writing in the console window.

        entrybox = tk.Frame(confrm)
        entrybox.pack(fill='x')

        tk.Label(entrybox, text='>', font=('Consolas', 11)).pack(side='left', padx=(5,2))
        self._entry = tk.Entry(entrybox, font=('Consolas', 11))
        self._entry.pack(side='left', fill='x', expand=True, padx=(0,5))
        self._entry.bind("<Return>", self._execute)


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

    def _set_genfrm(self):
        '''
        Sets up all the widgets within the general [DEFAULT] settings section.
        Binds the general settings StringVars to the widgets. This must be redone if
        the general settings dictionary is recreated.
        '''
        self._clear_frame(self._genfrm)
        d = self._widget_dict['general']
        # Setpoint wait
        ttk.Label(self._genfrm, text='Setpoint wait time [s]: ').grid(column=0, row=1, sticky='e')
        ttk.Entry(self._genfrm, textvariable=d['setpoint_wait']).grid(column=1, row=1, sticky='w')

        # Sample rate
        ttk.Label(self._genfrm, text='Sample rate [Hz]: ').grid(column=0, row=2, sticky='e')
        ttk.Entry(self._genfrm, textvariable=d['sample_rate']).grid(column=1, row=2, sticky='w')

        # Setpoint settle
        ttk.Label(self._genfrm, text='Setpoint settling time [s]: ').grid(column=0, row=3, sticky='e')
        ttk.Entry(self._genfrm, textvariable=d['setpoint_settle']).grid(column=1, row=3, sticky='w')

        # Setpoint timeout
        ttk.Label(self._genfrm, text='Setpoint timeout [s]: ').grid(column=0, row=4, sticky='e')
        ttk.Entry(self._genfrm, textvariable=d['setpoint_timeout']).grid(column=1, row=4, sticky='w')

        # Number of setpoints
        ttk.Label(self._genfrm, text='Number of setpoints: ').grid(column=0, row=5, sticky='e')
        ttk.Entry(self._genfrm, textvariable=d['num_setpoints']).grid(column=1, row=5, sticky='w')

        # Autotune each setpoint
        ttk.Label(self._genfrm, text='Autotune each setpoint? ').grid(column=0, row=6, sticky='e')
        ttk.Checkbutton(self._genfrm, variable=d['autotune_each'], offvalue='no', onvalue='yes').grid(column=1, row=6, sticky='w')

        # Units
        ttk.Label(self._genfrm, text='Pressure units: ').grid(column=0, row=7, sticky='e')
        ttk.Combobox(
            self._genfrm, 
            textvariable=d['unit'], 
            values=list(UNITS.values()), 
            state='readonly'
        ).grid(column=1, row=7, sticky='w')
        ttk.Button(self._genfrm, text='Apply Units', command=self._set_unit).grid(
            column=0, row=8, columnspan=2, padx=10, pady=(5, 0)
        )

    def _set_spfrm(self):
        '''
        In the future, I will make the `self._spfrm` frame into a canvas, in order to add scrolling if too many 
        setpoints are added to display at once on the screen.
        '''
        self._clear_frame(self._spfrm)
        d = self._widget_dict
        num_setpoints = self.config.getg('num_setpoints', cast=int)
        spfrms = {}
        for i in range(num_setpoints):
            spfrms[i+1] = ttk.LabelFrame(self._spfrm, text=f'Setpoint {i+1}')
            spfrms[i+1].grid(column=0, row=i)

            # Setpoint pressure

            ttk.Label(
                spfrms[i+1], 
                text = f'Setpoint pressure [{d['general']['unit'].get()}]: '
            ).grid(column=0, row=0, sticky='e')

            ttk.Entry(
                spfrms[i+1], 
                textvariable=d[f'setpoint.{i+1}']['pressure']
            ).grid(column=1, row=0, sticky='w')

            # Setpoint error tolerance
            ttk.Label(
                spfrms[i+1], 
                text = f'Setpoint error tolerance [{d['general']['unit'].get()}]: '
            ).grid(column=0, row=1, sticky='e')

            ttk.Entry(
                spfrms[i+1], 
                textvariable=d[f'setpoint.{i+1}']['max_err']
            ).grid(column=1, row=1, sticky='w')

    def _clear_frame(self, frame):
        for child in frame.winfo_children():
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
        self._set_genfrm() # Refresh the general settings frame to match the new config.
        self._set_spfrm() # Refresh the setpoint settings frame to match the new config.

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

    def _set_config_dict(self):
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

        :param skip: (tuple) list of sections to skip when applying changes. Mainly used to skip the 'units' setting.
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
        self._set_genfrm()
        self._set_spfrm()

        # Set the units on the PLC.
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
            self._message(f'[STATUS] Opened configuration file {load_path}')
            self._configpath.set(load_path)
            # reset the settings dictionaries using the new config
            self._get_config_dict()
            # Refresh the settings windows
            self._set_genfrm()
            self._set_spfrm()

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
            self._message('[STATUS] Save cancelled.')
        elif not save_path.endswith('.ini'):
            self._message('[WARNING] Configuration file not saved as .ini. Cancelling...')
        else:
            self.config.save(save_path)
            self._configpath.set(save_path)
            self._message('[STATUS] Configuration saved.')

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
            self._log(f'[STATUS] Calibration data saved to {self._resultspath.get()}')

        def worker():
            try:
                cal_seq = CalibrationSequence(
                    self.plc,
                    self.config,
                    self._widget_dict['general']['unit'].get(),
                    self._log_from_thread
                )

                results = cal_seq.run()

                save_path = self._resultspath.get()

                if save_path.endswith(".csv"):
                    results.to_csv(save_path, index=False)
                elif save_path.endswith(".xlsx"):
                    results.to_excel(save_path, index=False)

            except Exception as e:
                self._log_from_thread(f"[ERROR] {e}")

            finally: 
                # When the worker is finished (i.e. calibration sequence complete), the
                # built-in `.after` method of the Tk class will call this function in the
                # main thread immediately/as soon as the main thread is available ("after
                # 0 seconds")
                self.after(0, callback)

        # Only proceed if the calibration isn't already in progress.
        if self.is_busy:
            self._log('[STATUS] Calibration already in progress.')
            return
        
        # Only proceed if the user selected a valid save path.
        save_path = self._resultspath.get()
        save_dir, save_filename = os.path.split(save_path)
        if not save_path:
            self._log('[WARNING] No save path selected.')
            return
        if not save_filename.endswith(('.csv', '.xlsx')):
            self._log('[WARNING] Invalid save file format. Please select a .csv or .xlsx file.')
            return
        if not os.path.isdir(save_dir):
            self._log('[WARNING] Invalid save directory.')
            return

        # Start the calibration
        self.is_busy = True
        self._progressbar.start()
        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    # -------------------------------------------------------------------------------------------------------------------------

    # Embedded cli commands
    # ~~~~~~~~~~~~~~~~~~~~~
    
    def _log(self, msg):
        '''
        Sends a message to the console window.
        '''
        self._console.config(state='normal')
        self._console.insert(tk.END, msg+'\n')
        self._console.see(tk.END)
        self._console.config(state='disabled')

    def _log_from_thread(self, msg):
        '''
        Safely logs messages from worker threads by scheduling them on the Tk main thread.
        '''
        self.after(0, lambda: self._log(msg))

    def _execute(self, event=None):
        raw = self._entry.get()
        if not raw:
            return
        self._entry.delete(0, tk.END)

        command, *args = raw.split(' ')

        self._log(f'>{raw}')

        cmd_func = self._commands.get(command)
        if cmd_func:
            cmd_func(args)
        else:
            self._log('[WARNING] Unknown command.')

    def _cmd_shutdown(self, args=None):
        '''
        Safely closes the program. Activated either by the red X in the GUI
        or the `stop` command in the CLI.

        * I'm not sure how the `stop` command will function now that CLI commands are 
        being executed on a separate thread. Maybe it will still work?
        '''
        if args and args[0] == 'hard':
            self._log('[STATUS] Aborting...')
        elif self.is_busy:
            self._log('[WARNING] Calibration in progress. Please wait for it to finish before closing the program.')
            return
        else:
            self._log('[STATUS] Exiting...')

        self.plc.close()
        self.quit()
        self.destroy()
        sys.exit()
    
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
        self._log(f'System using pressure units: {self.widget_dict["general"]["unit"].get()}')
        transducers = ['MKS 1 pressure', 'MKS 2 pressure', 'MKS 3 pressure']
        for t in transducers:
            value = self.plc.read_float(ADDRESSES[t])
            self._log(f'{t}: {value:.2f} {self.widget_dict["general"]["unit"].get()}')

    def _cmd_bypass(self, args=None):
        '''
        Bypasses the startup sequence in UniLogic.
        '''
        self.plc.write_coil(ADDRESSES['bypass_startup'], value=True)

    def _cmd_help(self, args=None):
        '''
        Lists available commands in the embedded CLI.
        '''
        self._log('Available commands:')
        for cmd in self._commands.keys():
            self._log(f'  {cmd}')

    def _cmd_echo(self, args):
        '''
        Echoes the input arguments back to the console.
        '''
        self._log(' '.join(args))

    def _cmd_make_busy(self, args=None):
        '''
        For testing purposes
        '''
        if self.is_busy:
            self.is_busy = False
        else:
            self.is_busy = True




    # -------------------------------------------------------------------------------------------------------------------------

    # (DEPRECATED) configuration settings methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _initddict(self):
        '''
        Retrieves the ddict from the config and converts every string value to a tkinter StringVar.

        Only use this initially! once self.dconfig references the StringVars, they can't be reassigned.
        '''
        dconfig_Strings = self.config.getddict()
        dconfig_StringVars = {}
        for config_key, config_val in dconfig_Strings.items():
            dconfig_StringVars[config_key] = tk.StringVar(value=config_val)
        self._dconfig = dconfig_StringVars
    
    def _initspdicts(self):
        '''
        Reads the setpoint dicts from the loaded config (if it exists) or the default options (one setpoint).

        Unlike ._initddict(), this one can be called again for a new or updated configuration since the whole
        ._spfrm window is regenerated with new widgets, which can be bound to the new StringVars.
        '''
        sp_dict_Strings = self.config.getspdicts()
        sp_dict_StringVars = {}
        for sp_key, spconfig_Strings in sp_dict_Strings.items():
            spconfig_StringVars = {}
            sp_dict_StringVars[sp_key] = spconfig_StringVars
            for config_key, config_val in spconfig_Strings.items():
                sp_dict_StringVars[sp_key][config_key] = tk.StringVar(value=config_val)
        self._spconfigs = sp_dict_StringVars

    def _setddict(self):
        '''
        Used to apply changes to the settings made in the GUI
        Sends the altered StringVar ddict back to the config as a plain String ddict.

        If an incorrect value has been entered (i.e., someone enteres a letter instead of
        a number), the value won't be updated.
        '''
        dconfig_Strings = {}
        for config_key, config_val in self._dconfig.items():
            dconfig_Strings[config_key] = config_val.get() # Convert from tk.StringVars to normal Strings
        self.config.setddict(dconfig_Strings)

