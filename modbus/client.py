#modbus/client.py
from pymodbus.client import ModbusTcpClient
from utils.modbus_helpers import read_float, write_float
from utils.constants import ADDRESSES, UNITS

# Establishes communications with the PLC as modbus slave
class Slave:
    '''
    This basically is an improved version of the global `slave` object in CalCart.py.
    It self-handles connection/errors on initialization, and you can use the read/write methods
    for self-contained communication.

    Also, the .master attribute is basically adding the slave's master as an attribute
    (or the server's client as an attribute if you prefer)

    :param ip: (str) UniStream panel IP address
    '''
    def __init__(self, ip):
        self.master = ModbusTcpClient(ip, timeout=3)
        
    def connect(self):
        if not self.master.connect():
            raise ConnectionError('PLC connection failed.')
        # Stop users from changing units on the PLC once they can be changed from the GUI.
        self.write_coil(ADDRESSES['change_units_enabled'], value=False) 

    def read_float(self, address):
        '''
        Reads and translates floats from the respective modbus address.
        Excepts read errors as RuntimeError (I think this will not crash the
        program? hopefully.)

        :param address: The modbus address which is assigned in UniLogic.
        '''
        resp = self.master.read_input_registers(address=address, count=2)
        if resp.isError():
            raise RuntimeError(f'Read error: {resp}')
        return read_float(resp.registers)
    
    def write_float(self, address, value):
        '''
        Does the opposite of read_float.
        Hopefully the fact that the names here are identical to the 
        `utils.modbus_helpers` ones is not an issue...

        :param address: The modbus address which is assigned in UniLogic.
        '''
        regs = write_float(value)
        self.master.write_registers(address=address, values=regs)

    def read_coil(self, address):
        '''
        Reads boolean values from the respective modbus address.
        '''
        resp = self.master.read_coils(address=address, count=1)
        if resp.isError():
            raise RuntimeError(f'Read error: {resp}')
        return resp.bits[0]
    
    def write_coil(self, address, value):
         '''
         You get the idea.
         '''
         self.master.write_coil(address=address, value=value)

    def get_units(self):
        '''
        Reads the 16-bit Int (INT16) which represents the active unit.
        '''
        resp = self.master.read_input_registers(address=ADDRESSES['pressure_units'])
        if resp.isError():
            raise RuntimeError(f'Read error: {resp}')
        else:
            idx = resp.registers[0]
            return UNITS[idx]
        
    def set_units(self, new_unit):
        '''
        Sets the active pressure units in UniLogic.

        :param new_unit: str (must be one of the values in UNITS)
        '''
        if new_unit not in UNITS.values():
            raise ValueError(f'Invalid unit: {new_unit}. Must be one of {list(UNITS.values())}')
        
        idx = next(key for key, value in UNITS.items() if value == new_unit)

        self.master.write_register(address=ADDRESSES['pressure_units'], value=idx)


    def close(self):
        self.master.close()