#gui/frames

# Local
from config.settings import SETTINGS
from utils.constants import UNITS, STANDARDS

# Other
import tkinter as tk
from tkinter import ttk

def clear(frm):
    for child in frm.winfo_children():
        child.destroy()

def make_mousewheel_scrollable(canvas):
    '''
    Allows the mouse wheel to scroll the settings frames.
    '''
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>",
                        lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>",
                        lambda e: canvas.yview_scroll(1, "units"))

    def _unbind(event):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    canvas.bind("<Enter>", _bind)
    canvas.bind("<Leave>", _unbind)


class FileFrame(ttk.LabelFrame):
    '''
    Subframe in the top left/middle section of the GUI.
    (derived from `ttk.FileFrame`)

    __init__ parameters:
    :param root: GUI object (derived from `tk.Tk`)
    '''
    def __init__(self, root):
        self.root = root
        parent = root.frame

        super().__init__(
            parent,
            text='File',
            padding='10'
        )

        self.grid(column=0, row=0, columnspan=2, sticky="ew")
        self.columnconfigure(1, weight=1)
        self.grid_propagate(False)
        self.configure(width=800, height=120)

        self.refresh()

    def refresh(self):
        '''
        Sets or refreshes the frame widgets.
        '''
        # Load config button
        ttk.Button(self, text='Load Configuration', command=self.root.load_config, width='20').grid(column=0, row=0)
        ttk.Label(self, textvariable=self.root.configpath, anchor="w").grid(column=1, row=0, sticky="ew")

        # Save data button
        ttk.Button(self, text='Results Directory', command=self.root.choose_resultspath, width='20').grid(column=0, row=1)
        ttk.Label(self, textvariable=self.root.resultspath, anchor="w").grid(column=1, row=1, sticky="ew")

        # Save buttons
        ttk.Button(self, text='Apply Changes', command=self.root.widgets_to_config).grid(column=0, row=2, sticky='w')
        ttk.Button(self, text='Save Configuration', command=self.root.save_config).grid(column=1, row=2, sticky='w')


class GeneralSettingsFrame(ttk.LabelFrame):
    '''
    Subframe in the bottom left column of the GUI.

    Scrollable list of all user options besides individual setpoint settings.
    '''
    def __init__(self, root):
        self.root = root
        parent = root.frame

        super().__init__(
            parent,
            text='Calibration Sequence Options',
            padding='10'
        )

        self.grid(column=0, row=1, sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.grid_propagate(False)
        self.configure(width=400, height=300)

        canvas = tk.Canvas(self)
        canvas.pack(side='left', fill='both', expand=True)

        scrollbar = tk.Scrollbar(self, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')

        canvas.configure(yscrollcommand=scrollbar.set)

        make_mousewheel_scrollable(canvas)

        self.scrollable = tk.Frame(canvas)

        canvas.create_window((0, 0), window=self.scrollable, anchor='nw')
        self.scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self.refresh()


    def refresh(self):
        '''
        Sets up all the widgets for user settings in the [general], [customer], [device_info], 
        and [standard_info] sections of the config. Binds the StringVars to the widgets. This 
        must be redone if the config dictionary is recreated.
        '''
        clear(self.scrollable)

        # --------------------
        # [general]
        # --------------------

        d = self.root.widget_dict['general']

        # Section title
        ttk.Label(
            self.scrollable, text='General Settings', font=('TkDefaultFont', 10, 'bold')
        ).pack(fill='x', pady=(0, 5))

        for s in [s for s in SETTINGS if s.section == 'general']:
            if s.widget_type == 'entry':
                self._entry(s.label, s.section, s.key)
            elif s.widget_type == 'checkbutton':
                self._checkbutton(s.label, s.section, s.key)

        

        # Units
        row = ttk.Frame(self.scrollable)
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

        btnrow = ttk.Frame(self.scrollable)
        btnrow.pack(fill='x', pady=2)
        ttk.Button(
            btnrow, text='Apply Units', command=self.root.set_unit
        ).pack(fill='x', pady=(5, 0))

        # --------------------
        # [report.header]
        # --------------------

        # Section title
        ttk.Label(
            self.scrollable, text='Customer Information', font=('TkDefaultFont', 10, 'bold')
        ).pack(fill='x', pady=(0, 5))

        for s in SETTINGS:
            if s.section == 'report.header' and s.widget_type == 'entry':
                self._entry(s.label, s.section, s.key)

        # --------------------
        # [report.device]
        # --------------------

        # Section title
        ttk.Label(
            self.scrollable, text='Customer Device (UUT) Information', font=('TkDefaultFont', 10, 'bold')
        ).pack(fill='x', pady=(0, 5))

        for s in SETTINGS:
            if s.section == 'report.device' and s.widget_type == 'entry':
                self._entry(s.label, s.section, s.key)

        # --------------------
        # [report.standard]
        # --------------------

        d = self.root.widget_dict['report.standard']

        # Section title
        ttk.Label(
            self.scrollable, text='Standard/Reference Information', font=('TkDefaultFont', 10, 'bold')
        ).pack(fill='x', pady=(0, 5))

        # Standard presets
        row = ttk.Frame(self.scrollable)
        row.pack(fill='x', pady=2)
        ttk.Label(
            row, text='Standard Preset', width=24, anchor='e'
        ).pack(side='left')
        ttk.Combobox(
            row, 
            textvariable=d['preset'], 
            values=list(STANDARDS.keys()), 
            state='readonly'
        ).pack(side='left', fill='x', expand=True)

        btnrow = ttk.Frame(self.scrollable)
        btnrow.pack(fill='x', pady=2)
        ttk.Button(
            btnrow, text='Apply Preset', command=self.root.set_standard_preset
        ).pack(fill='x', pady=(5, 0))

        # Other info
        for s in SETTINGS:
            if s.section == 'report.standard' and s.widget_type == 'entry':
                self._entry(s.label, s.section, s.key)



    def _entry(self, label, ini_section, ini_key):
        '''
        Creates and packs a new setting to the table.
        Only used for generic string entry type settings. The rest you gotta do yourself.
        '''
        w = 24 # 34 for setpoint settings
        row = ttk.Frame(self.scrollable)
        row.pack(fill='x', pady=2)
        ttk.Label(
            row, text=label, width=w, anchor='e'
        ).pack(side='left')
        ttk.Entry(
            row, 
            textvariable=self.root.widget_dict[ini_section][ini_key]
        ).pack(side='left', fill='x', expand=True)

    def _checkbutton(self, label, ini_section, ini_key):
        '''
        Same thing as above but for yes/no check mark settings
        '''
        row = ttk.Frame(self.scrollable)
        row.pack(fill='x', pady=2)
        ttk.Label(
            row, text=label, width=24, anchor='e'
        ).pack(side='left')
        ttk.Checkbutton(
            row, 
            variable=self.root.widget_dict[ini_section][ini_key], 
            offvalue='no', 
            onvalue='yes'
        ).pack(side='left', fill='x', expand=True)

class SetpointSettingsFrame(ttk.LabelFrame):
    '''
    Same thing but for setpoint settings.
    '''
    def __init__(self, root):
        self.root = root
        parent = root.frame

        super().__init__(
            parent,
            text='Setpoint Options',
            padding='10'
        )

        self.grid(column=1, row=1, sticky='nsew')
        self.columnconfigure(1, weight=1)
        self.grid_propagate(False)
        self.configure(width=400, height=300)

        canvas = tk.Canvas(self)
        canvas.pack(side='left', fill='both', expand=True)

        scrollbar = tk.Scrollbar(self, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')

        canvas.configure(yscrollcommand=scrollbar.set)

        make_mousewheel_scrollable(canvas)

        self.scrollable = tk.Frame(canvas)

        canvas.create_window((0, 0), window=self.scrollable, anchor='nw')
        self.scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self.refresh()

    def refresh(self):
        '''
        Sets up the widgets in the setpoint frame.
        '''
        clear(self.scrollable)

        cf = self.root.config
        num_setpoints = cf.getg('num_setpoints', cast=int)

        for i in range(num_setpoints):

            # Section title
            ttk.Label(
                self.scrollable, text=f'Setpoint {i+1}', font=('TkDefaultFont', 10, 'bold')
            ).pack(fill='x', pady=(0, 5))

            # Setpoint pressure
            self._entry(
                f'Setpoint pressure [{cf.getg("unit", cast=str)}]: ',
                f'setpoint.{i+1}',
                'pressure'
            )

            # Setpoint error tolerance
            self._entry(
                f'Setpoint error tolerance [{cf.getg("unit", cast=str)}]: ',
                f'setpoint.{i+1}',
                'max_err'
            )

    def _entry(self, label, ini_section, ini_key):
        '''
        Creates and packs a new setting to the table.
        Only used for generic string entry type settings. The rest you gotta do yourself.
        '''
        w = 34 
        row = ttk.Frame(self.scrollable)
        row.pack(fill='x', pady=2)
        ttk.Label(
            row, text=label, width=w, anchor='e'
        ).pack(side='left')
        ttk.Entry(
            row, textvariable=self.root.widget_dict[ini_section][ini_key]
        ).pack(side='left', fill='x', expand=True)


class CalibrationRunFrame(ttk.Frame):
    '''
    Derived from the `ttk.Frame` class.
    '''
    def __init__(self, root):
        self.root = root
        parent = root.frame

        super().__init__(
            parent,
            padding='10'
        )

        self.grid(column=2, row=0, sticky='nsew')

        self.refresh()

    def refresh(self):
        '''
        Instantiates the `progressbar` attribute which can be 
        started/stopped to indicate that a calibration sequence is in progress. 
        '''
        ttk.Button(
            self, text='Run\nCalibration\nSequence', command=self.root.cal
        ).grid(column=0, row=0, rowspan=2, padx=10, sticky='ns')

        ttk.Label(self, textvariable=self.root.statusvar).grid(column=1, row=0)
        self.progressbar = ttk.Progressbar(self, orient='horizontal', mode='indeterminate', length=350)
        self.progressbar.grid(column=1, row=1, pady=5, padx=10)
    
    def start_anim(self):
            self.progressbar.start()

    def stop_anim(self):
        self.progressbar.stop()

