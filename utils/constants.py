#utils/constants.py

# Modbus address dictionary (dict key == UniLogic variable name)
ADDRESSES = {
    'submit_setpoint': 0,
    'run_autotune': 1,
    'run_PID': 2,
    'PID Configuration.Autotune Done': 3,
    'MKS 1 pressure': 100,
    'MKS 2 pressure': 102,
    'MKS 3 pressure': 104,
    'MKS Zero pressure': 106,
    'Setpoint pressure': 108,
    'pressure_units': 110,
    'UUT pressure': 111
}

# Pressure units dictionary (dict key == value of pressure_units variable in UniLogic)
UNITS = {
    0: 'Torr',
    1: 'micron',
    2: 'bar',
    3: 'mbar',
    4: 'Pascal',
    5: 'kPa'
}