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
    :param addresses: ...
    :param unit: ...
    '''
    def __init__(self, plc, config, ADDRESSES, unit):
        super().__init__() # Initialize the parent class

        # Setup gui window
        self.title("CalCart 2025 IMA Life North America")
        self.iconbitmap("./gui/logo.ico")

        # Initialize object references
        self.plc = plc # stateful reference to variable `plc` in main
        self.config = config # stateful reference to variable `config` in main
        self.ad = ADDRESSES
        self.unit = unit

        # Get initial values from the config ddict, then convert them to tkinter StringVars.
        self._initddict() # --dict of DEFAULT section of config INI
        # Get the INI path as a StringVar
        if self.config.path is not None:
            self.configpath = tk.StringVar(value=self.config.path)
        else:
            self.configpath = tk.StringVar(value='<--- Select a configuration.')
        # Initialize save results directory
        self.resultspath = tk.StringVar(value="<--- Choose where to save calibration data.")

        # Make the frame
        self.frm = ttk.Frame(self, padding='10')
        self.frm.pack(fill='both', expand=True)
        self.frm.columnconfigure(0, weight=0)  # left side stays fixed
        self.frm.columnconfigure(1, weight=1)  # right side expands
        self.frm.rowconfigure(1, weight=1)
        # Make file subframe
        self.filefrm = ttk.LabelFrame(self.frm, text='File', padding='10')
        # Make settings subframe
        self.setfrm = ttk.LabelFrame(self.frm, text="Calibration Sequence Options", padding='10')
        # Format subframes
        self.filefrm.grid(column=0, row=0, sticky="ew")
        #self.setfrm.grid(column=0, row=1, sticky="ew")
        self.setfrm.grid(column=0, row=1, sticky="nsew")
        self.filefrm.columnconfigure(1, weight=1)
        self.setfrm.columnconfigure(1, weight=1)
        #self.filefrm.grid_propagate(False)
        #self.filefrm.configure(width=400)
        #self.setfrm.grid_propagate(False)
        #self.setfrm.configure(width=400)

        self.filefrm.grid_propagate(False)
        self.filefrm.configure(width=400, height=120)

        self.setfrm.grid_propagate(False)
        self.setfrm.configure(width=400, height=300)




        # ------------------------------------------------------------------------

        # Add GUI elements
        # ~~~~~~~~~~~~~~~~

        # --File--
        # Load config button
        ttk.Button(self.filefrm, text='Load Configuration', command=self._load_config, width='20').grid(column=0, row=0)
        ttk.Label(self.filefrm, textvariable=self.configpath, anchor="w").grid(column=1, row=0, sticky="ew")

        # Save data button
        ttk.Button(self.filefrm, text='Results Directory', command=self._choose_resultspath, width='20').grid(column=0, row=1)
        ttk.Label(self.filefrm, textvariable=self.resultspath, anchor="w").grid(column=1, row=1, sticky="ew")


        # --Settings--
        # Setpoint wait
        ttk.Label(self.setfrm, text='Setpoint wait time [s]: ').grid(column=0, row=1, sticky='e')
        ttk.Entry(self.setfrm, textvariable=self.dc['setpoint_wait']).grid(column=1, row=1, sticky='w')

        # Sample rate
        ttk.Label(self.setfrm, text='Sample rate [Hz]: ').grid(column=0, row=2, sticky='e')
        ttk.Entry(self.setfrm, textvariable=self.dc['sample_rate']).grid(column=1, row=2, sticky='w')

        # Setpoint settle
        ttk.Label(self.setfrm, text='Setpoint settling time [s]: ').grid(column=0, row=3, sticky='e')
        ttk.Entry(self.setfrm, textvariable=self.dc['setpoint_settle']).grid(column=1, row=3, sticky='w')

        # Setpoint timeout
        ttk.Label(self.setfrm, text='Setpoint timeout [s]: ').grid(column=0, row=4, sticky='e')
        ttk.Entry(self.setfrm, textvariable=self.dc['setpoint_timeout']).grid(column=1, row=4, sticky='w')

        # Number of setpoints
        ttk.Label(self.setfrm, text='Number of setpoints: ').grid(column=0, row=5, sticky='e')
        ttk.Entry(self.setfrm, textvariable=self.dc['num_setpoints']).grid(column=1, row=5, sticky='w')

        # Autotune each setpoint
        ttk.Label(self.setfrm, text='Autotune each setpoint? ').grid(column=0, row=6, sticky='e')
        ttk.Checkbutton(self.setfrm, variable=self.dc['autotune_each'], offvalue='no', onvalue='yes').grid(column=1, row=6, sticky='w')

        # Save buttons
        ttk.Button(self.setfrm, text='Apply Changes', command=self._setddict).grid(column=0, row=7)
        ttk.Button(self.setfrm, text='Save Configuration', command=self._save_config).grid(column=1, row=7)


        # --Run--
        # Make calibration subframe
        self.calfrm = ttk.Frame(self.frm, padding='10')
        self.calfrm.grid(column=1, row=0)
        ttk.Button(self.calfrm, text='Run\nCalibration\nSequence', command=self._cal).grid(column=0, row=0)
        ttk.Label(self.calfrm, text='This will eventually be a status update box').grid(column=0, row=1)

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
            self.configpath.set(load_path)
            # Update self.dc without breaking references
            dc_new = self.config.getddict()
            for key, val in dc_new.items():
                if key in self.dc:
                    self.dc[key].set(val)


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

        Only use this initially! once self.dc references the StringVars, they can't be reassigned.
        '''
        dc_Strings = self.config.getddict()
        dc_StringVars = {}
        for key, val in dc_Strings.items():
            dc_StringVars[key] = tk.StringVar(value=val)
        self.dc = dc_StringVars
    
    def _setddict(self):
        '''
        Used to apply changes to the settings made in the GUI
        Sends the altered StringVar ddict back to the config as a plain String ddict.
        '''
        dc_Strings = {}
        for key, val in self.dc.items():
            dc_Strings[key] = val.get() # Convert from tk.StringVars to normal Strings
        self.config.setddict(dc_Strings)

    def _choose_resultspath(self):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes = [("comma-separated value file", "*.csv"), ("Excel file", "*.xlsx")]
        )
        self.resultspath.set(save_path)
    
    def _cal(self):
        '''
        For now I will assume the save path is valid; eventually I will add a popup warning if it is not.
        '''
        cal_seq = CalibrationSequence(self.plc, self.config, self.ad, self.unit)
        results = cal_seq.run()
        # Save results
        save_path = self.resultspath.get()
        if save_path.endswith(".csv"):
            results.to_csv(save_path)
        elif save_path.endswith(".xlsx"):
            results.to_excel(save_path)
        else:
            print('[WARNING] Incorrect file type; aborting save.')