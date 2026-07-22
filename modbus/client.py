#modbus/client.py
from pymodbus.client import ModbusTcpClient
import threading
import time
from utils.modbus_helpers import (
    read_float, 
    write_float, 
    read_int32,
    requires_connection,
)
from utils.constants import ADDRESSES, UNITS

class Slave:
    '''
    This basically is an improved version of the global `slave` object in CalCart.py.
    It self-handles connection/errors on initialization, and you can use the read/write methods
    for self-contained communication.

    Also, the .master attribute is basically adding the slave's master as an attribute
    (or the server's client as an attribute if you prefer)

    __init__ parameters:
    :param ip: (str) UniStream panel IP address
    '''
    def __init__(self, ip):
        self.master = ModbusTcpClient(ip, timeout=3)
        self._lock = threading.Lock()
        self.connected = False
        
    def connect(self):
        '''
        Attempt to connect to the PLC if not already connected.
        If connection fails: the method returns None, `self.connected`
        remains False and all read/write methods will be disabled.
        '''
        if self.connected:
            return
        
        if not self.master.connect():
            raise ConnectionError('Failed to connect to PLC.')

        # Stop users from changing units on the PLC once they can be changed from the GUI.
        with self._lock:
            resp = self.master.write_coil(
                ADDRESSES['change_units_enabled'],
                value=False
            )

            if resp.isError():
                raise ConnectionError('Failed to connect to PLC.')
        
        self.connected = True

    @requires_connection
    def read_float(self, address):
        '''
        Reads and translates floats from the respective modbus address.
        Excepts read errors as RuntimeError (I think this will not crash the
        program? hopefully.)

        :param address: The modbus address which is assigned in UniLogic.
        '''
        with self._lock:
            resp = self.master.read_input_registers(address=address, count=2)

            if resp.isError():
                raise ConnectionError(f'Read error: {resp}')
            
            return read_float(resp.registers)
    
    @requires_connection
    def write_float(self, address, value):
        '''
        Does the opposite of read_float.
        Hopefully the fact that the names here are identical to the 
        `utils.modbus_helpers` ones is not an issue...

        :param address: The modbus address which is assigned in UniLogic.
        '''
        with self._lock:
            regs = write_float(value)
            resp = self.master.write_registers(address=address, values=regs)

            if resp.isError():
                raise ConnectionError(f'Write error: {resp}')

    @requires_connection
    def read_coil(self, address):
        '''
        Reads boolean values from the respective modbus address.
        '''
        with self._lock:
            resp = self.master.read_coils(address=address, count=1)

            if resp.isError():
                raise ConnectionError(f'Read error: {resp}')
            
            return resp.bits[0]
    
    @requires_connection
    def write_coil(self, address, value):
         '''
         You get the idea.
         '''
         with self._lock:
            resp = self.master.write_coil(address=address, value=value)

            if resp.isError():
                raise ConnectionError(f'Write error: {resp}')

    @requires_connection
    def read_int32(self, address):
        '''
        Reads the 32-bit Int (INT16).
        '''
        with self._lock:
            resp = self.master.read_input_registers(address=address, count=2)

            if resp.isError():
                raise ConnectionError(f'Read error: {resp}')
            
            return read_int32(resp.registers)

    @requires_connection
    def get_units(self):
        '''
        Reads the 16-bit Int (INT16) which represents the active unit.
        '''
        with self._lock:
            resp = self.master.read_input_registers(address=ADDRESSES['pressure_units'])

            if resp.isError():
                raise ConnectionError(f'Read error: {resp}')
            
            idx = resp.registers[0]
            return UNITS[idx]
        
    @requires_connection
    def set_units(self, new_unit):
        '''
        Sets the active pressure units in UniLogic.

        :param new_unit: str (must be one of the values in UNITS)
        '''
        with self._lock:
            if new_unit not in UNITS.values():
                raise ValueError(f'Invalid unit: {new_unit}. Must be one of {list(UNITS.values())}')
            
            idx = next(key for key, value in UNITS.items() if value == new_unit)

            resp = self.master.write_register(address=ADDRESSES['pressure_units'], value=idx)

            if resp.isError():
                raise ConnectionError(f'Write error: {resp}')

    def monitor_pid_status(self, log_callback=print):
        '''
        Prints an update whenever the UniLogic PID status changes.
        (See UniLogic Help forms for status meaning)

        :param log: Callable to display update messages.
        '''
        def monitor():
            log_callback('[DEBUG] PID monitor thread started.')
            last_status = None
            while True:
                if self._lock.acquire(blocking=False):
                    #log_callback('[DEBUG] Acquired PID monitor lock.')
                    try:
                        resp = self.master.read_input_registers(
                            address=ADDRESSES['PID Configuration.Status'], 
                            count=1
                        )
                        
                        if resp.isError():
                            log_callback(f'[ERROR] {resp}')
                            continue
                        
                        pid_status = resp.registers[0]

                        #log_callback(f"[DEBUG] PID status raw value = {pid_status}")

                        if pid_status != last_status:
                            log_callback(f'[STATUS] PID Status update: {pid_status}')
                            last_status = pid_status

                    except Exception as e:
                        log_callback(f'[WARNING] PID monitor failed: {e}')

                    finally:
                        self._lock.release()

                # If lock wasn't available, just try later
                #else:
                    #log_callback('[DEBUG] PID monitor lock busy.')
                time.sleep(1.0)

        threading.Thread(
            target=monitor,
            daemon=True
        ).start()


    def close(self):
        self.connected = False
        self.master.close()