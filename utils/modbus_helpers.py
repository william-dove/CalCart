#utils/modbus_helpers.py
import struct
from functools import wraps

def read_float(regs, swapped=True):
    '''
    Modbus stores 32-bit floats in two separate registers which must be "translated" 
    into a normal floating point number.
    Translates a 2-register list into a python float32.
    The order of the two registers may be swapped; this is likely the case if the numbers are all weird.

    :param regs: list of two registers--the `.registers` attribute of the `slave.read_input_registers()` method.
    :return: 32-bit python float
    '''
    if swapped:
            regs = regs[::-1]
    packed = struct.pack('>HH', regs[0], regs[1])
    return struct.unpack('>f', packed)[0]

def write_float(value, swapped=True):
    '''
    Performs the reverse operation of read_float.
    Translates a normal python 32-bit float into a list of two registers for Modbus.

    :param value: 32-bit python float
    :return: packaged list of registers--pass into the `slave.write_registers()` method.
    '''
    packed = struct.pack('>f', value)
    regs = struct.unpack('>HH', packed)
    if swapped:
            regs = regs[::-1]
    return list(regs)

def read_int32(regs, swapped=True):
    if swapped:
        regs = regs[::-1]

    packed = struct.pack('>HH', regs[0], regs[1])
    return struct.unpack('>i', packed)[0]



def requires_connection(func):
    '''
    Decorator to check if the slave is connected before executing a method.

    If the slave is not connected, connection is attempted. If this fails, 
    the method will not be executed and will return None.
    '''
    @wraps(func) # Preserves docstrings etc.
    def wrapper(self, *args, **kwargs):
        self.connect() # Attempt reconnection
        
        try:
            return func(self, *args, **kwargs)
        
        except Exception:
             self.connected = False
             raise
        
    return wrapper