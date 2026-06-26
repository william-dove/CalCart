#gui/gui.py 
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

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

        # Initialize object references
        self.plc = plc # stateful reference to variable `plc` in main
        self.config = config # stateful reference to variable `config` in main
        self.ad = ADDRESSES
        self.unit = unit

        # Get initial values from the config ddict, then convert them to tkinter StringVars.
        self.dc = self._getddict() # --dict of DEFAULT section of config INI
        # Get the INI path as a StringVar
        if self.config.path is not None:
            self.configpath = tk.StringVar(value=self.config.path)
        else:
            self.configpath = tk.StringVar(value='<--- Select a configuration.')

        # Make the frame
        self.frm = tk.Frame(self)
        self.frm.grid() # Use grid to place objects (as opposed to .pack())

        # ------------------------------------------------------------------------

        # Add GUI elements
        # ~~~~~~~~~~~~~~~~

        # Load config button
        ttk.Button(self.frm, text="Load Configuration", command=self._load_config).grid(column=0, row=0)
        ttk.Label(self.frm, textvariable=self.configpath).grid(column=1, row=0)

        # Setpoint wait
        ttk.Label(self.frm, text='1. Setpoint wait time [s]: ').grid(column=0, row=1)
        ttk.Entry(self.frm, textvariable=self.dc['setpoint_wait']).grid(column=1, row=1)

        # Sample rate
        ttk.Label(self.frm, text='2. Sample rate [Hz]: ').grid(column=0, row=2)
        ttk.Entry(self.frm, textvariable=self.dc['sample_rate']).grid(column=1, row=2)

        # Setpoint settle
        ttk.Label(self.frm, text='3. Setpoint settling time [s]: ').grid(column=0, row=3)
        ttk.Entry(self.frm, textvariable=self.dc['setpoint_settle']).grid(column=1, row=3)

        # Setpoint timeout
        ttk.Label(self.frm, text='4. Setpoint timeout [s]: ').grid(column=0, row=4)
        ttk.Entry(self.frm, textvariable=self.dc['setpoint_timeout']).grid(column=1, row=4)

        # Number of setpoints
        ttk.Label(self.frm, text='5. Number of setpoints: ').grid(column=0, row=5)
        ttk.Entry(self.frm, textvariable=self.dc['num_setpoints']).grid(column=1, row=5)

        # Autotune each setpoint
        ttk.Label(self.frm, text='6. Autotune each setpoint? ').grid(column=0, row=6)
        ttk.Checkbutton(self.frm, variable=self.dc['autotune_each'], offvalue='no', onvalue='yes').grid(column=1, row=6)

        # Save buttons
        ttk.Button(self.frm, text='Apply Changes', command=self._setddict).grid(column=0, row=7)
        ttk.Button(self.frm, text='Save Configuration', command=self._save_config).grid(column=1, row=7)


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
        self.config.load(load_path)
        print(f'[STATUS] Opened configuration file {load_path}')
        self.configpath.set(load_path)
        self._getddict()

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

    def _getddict(self):
        '''
        Retrieves the ddict from the config and converts every string value to a tkinter StringVar.
        '''
        dc_Strings = self.config.getddict()
        dc_StringVars = {}
        for key, val in dc_Strings.items():
            dc_StringVars[key] = tk.StringVar(value=val)
        return dc_StringVars
    
    def _setddict(self):
        '''
        Used to apply changes to the settings made in the GUI
        Sends the altered StringVar ddict back to the config as a plain String ddict.
        '''
        dc_Strings = {}
        for key, val in self.dc.items():
            dc_Strings[key] = val.get() # Convert from tk.StringVars to normal Strings
        self.config.setddict(dc_Strings)