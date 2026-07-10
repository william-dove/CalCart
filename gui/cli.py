#gui/cli.py

# Other
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

class ConsoleFrame(ttk.LabelFrame):
    '''
    Console frame
    '''
    def __init__(self, root):
        '''
        The commands with a leading underscore are defined here. Those without a 
        leading underscore are defined in `gui.py`.
        '''
        self.root = root

        # Initialize command dictionary
        self.commands = {
            'help': self._help,
            'cls': self._clear,
            'echo': self._echo,
            'status': self.root.status,
            'stop': self.root.shutdown,
            'busy': self.root.make_busy,
            'bypass': self.root.bypass,
            'connect': self.root.connect,
            'report': self.root.report,
            'apply': self.root.widgets_to_config,
        }

        # Build window
        parent = root.frame
        super().__init__(
            parent,
            text='Console',
            padding='10'
        )

        self.grid(column=2, row=1, sticky='ns')

        self.refresh()

    def refresh(self):
        '''
        Instantiates the local attributes `console` and `entry` to be 
        used when handling/displaying command entries.
        '''
        self.console = ScrolledText(self, font=('Consolas', 11), height=12)
        self.console.pack(fill='both', expand=True)
        self.console.insert(tk.END, 'Application started.\n')
        self.console.config(state='disabled') # Stop the user from writing in the console window.

        entrybox = tk.Frame(self)
        entrybox.pack(fill='x')

        tk.Label(entrybox, text='>', font=('Consolas', 11)).pack(side='left', padx=(5,2))
        self.entry = tk.Entry(entrybox, font=('Consolas', 11))
        self.entry.pack(side='left', fill='x', expand=True, padx=(0,5))
        self.entry.bind("<Return>", self.execute)

    def log(self, msg):
        '''
        Sends a message to the console window.

        *Note: the `config` method here is a method stemming from the 
        `ScrolledText` tkinter class, not my `config` attribute of the GUI
        instance.
        '''
        self.console.config(state='normal')
        self.console.insert(tk.END, str(msg)+'\n')
        self.console.see(tk.END)
        self.console.config(state='disabled')

    def execute(self, event=None):
        raw = self.entry.get()
        if not raw:
            return
        self.entry.delete(0, tk.END)

        command, *args = raw.split(' ')

        self.log(f'>{raw}')

        cmd_func = self.commands.get(command)
        if cmd_func:
            cmd_func(args)
        else:
            self.log('[WARNING] Unknown command.')

    # Commands

    def _help(self, args=None):
        '''
        Lists available commands in the embedded CLI.
        '''
        self.log('Available commands:')
        for cmd in self.commands.keys():
            self.log(f'  {cmd}')

    def _clear(self, args=None):
        '''
        Clears the console window.
        '''
        self.console.config(state='normal')
        self.console.delete('1.0', tk.END)
        self.console.config(state='disabled')

    def _echo(self, args):
        '''
        Echoes the input arguments back to the console.
        '''
        self.log(' '.join(args))
