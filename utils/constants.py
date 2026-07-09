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

# Default values for the "DEFAULT" section of the config .ini
# This is now outdated; the dictionary config.settings.SETTINGS is preferred: it is a 
# dictionary of dataclass objects with various bits of information, including INI 
# section, INI key, default value, report excell cell (where applicable), description, etc.
# Still, I don't want to change the GUI code for the 100th time even if it would be more efficient, so I won't get rid of this.
DEFAULT_VALUES = {
    # [general]
    'setpoint_wait': '30', # [s] (general section)
    'sample_rate': '10', # [Hz] (general section)
    'setpoint_settle': '60', # [s] (general section) setpoint must be within tolerance for this much time to be considered "settled"
    'setpoint_timeout': '300', # [s] (general section)
    'num_setpoints':  '1', # (general section)
    'autotune_each': 'no', # (general section)
    'unit': 'Torr', # **Units set by the PLC**
    # [report]
    'company': 'Company Name',
    'project': 'Project Name',
    'service_number': 'Service Number',
    'machine': 'Machine Name',
    'location': 'Location',
    'date': 'Date',
    'calibration_type': 'Calibration Type',
    'procedure': 'Procedure',
    'calibration': 'Calibration',
    'dev_manufacturer': 'Manufacturer',
    'dev_model_number': 'Model Number',
    'dev_serial_number': 'Serial Number',
    'dev_tag_id_number': 'Tag/ID Number',
    'dev_range': 'Range',
    'dev_device_accuracy': 'Device Accuracy',
    'dev_output_signal': 'Output Signal',
    'std_calibration_date': 'Calibration Date',
    'std_calibration_due_date': 'Calibration Due Date',
    'std_standard_accuracy': 'Standard Accuracy',
    'std_accuracy_ratio': 'Accuracy Ratio',
    # [setpoint.i]
    'pressure': '1', # (setpoint section) Units set by the PLC
    'max_err': '0.05'
    
}