#utils/constants.py

# Modbus address dictionary (dict key == UniLogic variable name)
ADDRESSES = {
    'submit_setpoint': 0,
    'run_autotune': 1,
    'run_PID': 2,
    'PID Configuration.Autotune Done': 3,
    'bypass_startup': 4,
    'change_units_enabled': 5,
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

# Conversion factor from Torr to other units (how many units in 1 Torr)
CONVERSION = {
    'Torr': 1.0,
    'micron': 1000.0,
    'bar': 0.00133322,
    'mbar': 1.33322,
    'Pascal': 133.322,
    'kPa': 0.133322
}