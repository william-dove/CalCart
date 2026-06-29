#gui/gui.py 
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from calibration.calibration import CalibrationSequence

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
    def __init__(self, plc, config, ADDRESSES, unit):
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

        # Initialize object references
        self.plc = plc # stateful reference to variable `plc` in main
        self.config = config # stateful reference to variable `config` in main
        self.ad = ADDRESSES
        self.unit = unit

        # Initialize settings tk.StringVar dictionary
        self._initddict() # Copies the settings from the existing DEFAULT section of the current config
        # Get the INI path as a StringVar
        if self.config.path is not None: # If the user loaded a config path on startup, add it.
            self._configpath = tk.StringVar(value=self.config.path) 
        else: # If the user did not load a config path, use the defualt config settings and prompt the user to select a config file.
            self._configpath = tk.StringVar(value='<--- Select a configuration.')

        # Initialize save results directory
        self._resultspath = tk.StringVar(value="<--- Choose where to save calibration data.")

        # Initialise setpoint settings into tk.StringVar nested dictionary
        self._initspdicts()


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
        # File subframe (Top)
        filefrm = ttk.LabelFrame(frm, text='File', padding='10')
        filefrm.grid(column=0, row=0, columnspan=2, sticky="ew")
        filefrm.columnconfigure(1, weight=1)
        filefrm.grid_propagate(False)
        filefrm.configure(width=800, height=120)

        # General [DEFAULT] settings subframe (Bottom left)
        setfrm = ttk.LabelFrame(frm, text="Calibration Sequence Options", padding='10')
        setfrm.grid(column=0, row=1, sticky="nsew")
        setfrm.columnconfigure(1, weight=1)
        setfrm.grid_propagate(False)
        setfrm.configure(width=400, height=300)

        # Setpoint settings subframe (Bottom right)
        self._spfrm = ttk.LabelFrame(frm, text="Setpoints", padding='10')
        self._spfrm.grid(column=1, row=1, sticky='nsew')
        self._spfrm.columnconfigure(1, weight=1)
        self._spfrm.grid_propagate(False)
        self._spfrm.configure(width=400, height=300)

        # Calibration subframe (Far right)
        calfrm = ttk.Frame(frm, padding='10')
        calfrm.grid(column=2, row=0, rowspan=2, sticky='nsew')

        # ------------------------------------------------------------------------

        # Add GUI elements
        # ~~~~~~~~~~~~~~~~

        # --File--
        self._set_filefrm(filefrm)

        # --Settings--
        self._set_genfrm(setfrm)

        # --Setpoint Settings--
        self._set_spfrms()

        # --Run--
        ttk.Button(calfrm, text='Run\nCalibration\nSequence', command=self._cal).grid(column=0, row=0)
        ttk.Label(calfrm, text='This will eventually be a status update box').grid(column=0, row=1)

    # -----------------------------------------------------------------------------------------------------


    def _load_config(self):
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
        if load_path.endswith('.ini'):
            self.config.load(load_path)
            print(f'[STATUS] Opened configuration file {load_path}')
            self._configpath.set(load_path)
            # Update self._dconfig without breaking references
            dconfig_new = self.config.getddict()
            for key, val in dconfig_new.items():
                if key in self._dconfig:
                    self._dconfig[key].set(val)
            # Replace self._spconfigs with new references
            self._initspdicts()
            # Refresh/rebuild the setpoint settings window with the new references
            self._set_spfrms()

    def _save_config(self):
        '''
        Saves a config that has been edited in the GUI.
        '''
        # Apply changes
        self._setddict()
        # Save the configuration
        save_path = filedialog.asksaveasfilename(
            defaultextension='.ini',
            filetypes=[("INI file", "*.ini")]
        )
        if not save_path:
            print('[STATUS] Save cancelled.')
        elif not save_path.endswith('.ini'):
            print('[WARNING] Configuration file not saved as .ini. Cancelling...')
        else:
            self.config.save(save_path)
            print('[STATUS] Configuration saved.')

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

    def _initspdicts(self):
        '''
        Reads the setpoint dicts from the loaded config (if it exists) or the default options (one setpoint).

        Unlike ._initddict(), this one can be called again for a new or updated configuration since the whole
        ._spfrm window is regenerated with new widgets, which can be bound to the new StringVars.

        [FUTURE]: I should just do the same thing with the general settings to make things less confusing.
        '''
        sp_dict_Strings = self.config.getspdicts()
        sp_dict_StringVars = {}
        for sp_key, spconfig_Strings in sp_dict_Strings.items():
            spconfig_StringVars = {}
            sp_dict_StringVars[sp_key] = spconfig_StringVars
            for config_key, config_val in spconfig_Strings.items():
                sp_dict_StringVars[sp_key][config_key] = tk.StringVar(value=config_val)
        self._spconfigs = sp_dict_StringVars

    def _choose_resultspath(self):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes = [("comma-separated value file", "*.csv"), ("Excel file", "*.xlsx")]
        )
        self._resultspath.set(save_path)
    
    def _cal(self):
        '''
        For now I will assume the save path is valid; eventually I will add a popup warning if it is not.
        '''
        cal_seq = CalibrationSequence(self.plc, self.config, self.ad, self.unit)
        results = cal_seq.run()
        # Save results
        save_path = self._resultspath.get()
        if save_path.endswith(".csv"):
            results.to_csv(save_path)
        elif save_path.endswith(".xlsx"):
            results.to_excel(save_path)
        else:
            print('[WARNING] Incorrect file type; aborting save.')

    
    def _clear_frame(self, frame):
        for child in frame.winfo_children():
            child.destroy()

    def _set_spfrms(self):
        '''
        In the future, I will make the `self._spfrm` frame into a canvas, in order to add scrolling if too many 
        setpoints are added to display at once on the screen.
        '''
        self._clear_frame(self._spfrm)
        num_setpoints = self.config.getd('num_setpoints', cast=int)
        spfrms = {}
        for i in range(num_setpoints):
            spfrms[i+1] = ttk.LabelFrame(self._spfrm, text=f'Setpoint {i+1}')
            spfrms[i+1].grid(column=0, row=i)

            # Setpoint pressure
            ttk.Label(spfrms[i+1], text=f'Setpoint pressure [{self.unit}]: ').grid(column=0, row=0, sticky='e')
            ttk.Entry(spfrms[i+1], textvariable=self._spconfigs[f'setpoint.{i+1}']['pressure']).grid(column=1, row=0, sticky='w')

            # Setpoint error tolerance
            ttk.Label(spfrms[i+1], text=f'Setpoint error tolerance [{self.unit}]: ').grid(column=0, row=1, sticky='e')
            ttk.Entry(spfrms[i+1], textvariable=self._spconfigs[f'setpoint.{i+1}']['max_err']).grid(column=1, row=1, sticky='w')

    def _set_genfrm(self, setfrm):
        '''
        Sets up all the widgets within the general [DEFAULT] settings section.
        '''
        # Setpoint wait
        ttk.Label(setfrm, text='Setpoint wait time [s]: ').grid(column=0, row=1, sticky='e')
        ttk.Entry(setfrm, textvariable=self._dconfig['setpoint_wait']).grid(column=1, row=1, sticky='w')

        # Sample rate
        ttk.Label(setfrm, text='Sample rate [Hz]: ').grid(column=0, row=2, sticky='e')
        ttk.Entry(setfrm, textvariable=self._dconfig['sample_rate']).grid(column=1, row=2, sticky='w')

        # Setpoint settle
        ttk.Label(setfrm, text='Setpoint settling time [s]: ').grid(column=0, row=3, sticky='e')
        ttk.Entry(setfrm, textvariable=self._dconfig['setpoint_settle']).grid(column=1, row=3, sticky='w')

        # Setpoint timeout
        ttk.Label(setfrm, text='Setpoint timeout [s]: ').grid(column=0, row=4, sticky='e')
        ttk.Entry(setfrm, textvariable=self._dconfig['setpoint_timeout']).grid(column=1, row=4, sticky='w')

        # Number of setpoints
        ttk.Label(setfrm, text='Number of setpoints: ').grid(column=0, row=5, sticky='e')
        ttk.Entry(setfrm, textvariable=self._dconfig['num_setpoints']).grid(column=1, row=5, sticky='w')

        # Autotune each setpoint
        ttk.Label(setfrm, text='Autotune each setpoint? ').grid(column=0, row=6, sticky='e')
        ttk.Checkbutton(setfrm, variable=self._dconfig['autotune_each'], offvalue='no', onvalue='yes').grid(column=1, row=6, sticky='w')

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
        ttk.Button(filefrm, text='Apply Changes', command=self._setddict).grid(column=0, row=2, sticky='w')
        ttk.Button(filefrm, text='Save Configuration', command=self._save_config).grid(column=1, row=2, sticky='w')