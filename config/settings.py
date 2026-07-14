from dataclasses import dataclass

@dataclass(frozen=True)
class Setting:
    section: str
    key: str
    label: str
    default: str = ''
    widget_type: str = 'entry'
    report_cell: str = None


SETTINGS = [
    # --------------------
    # [general]
    # --------------------
    Setting(
        section="general",
        key="setpoint_wait",
        label="Setpoint wait time [s]",
        default="2",
    ),
    Setting(
        section="general",
        key="sample_rate",
        label="Sample rate [Hz]",
        default="10",
    ),
    Setting(
        section="general",
        key="setpoint_settle",
        label="Setpoint settling time [s]",
        default="60",
    ),
    Setting(
        section="general",
        key="setpoint_timeout",
        label="Setpoint timeout [s]",
        default="300",
    ),
    Setting(
        section="general",
        key="num_setpoints",
        label="Number of setpoints",
        default="1",
    ),
    Setting(
        section='general',
        key='num_test_units',
        label='Number of Test Units',
        default='1',
    ),
    Setting(
        section="general",
        key="autotune_each",
        label="Autotune each setpoint?",
        default="no",
        widget_type='checkbutton',
    ),
    Setting(
        section='general',
        key='uut_signal',
        label='Test Unit Plugged In',
        default='no',
        widget_type='checkbutton',
    ),
    Setting(
        section='general',
        key='manual_entry',
        label='Manual Setpoint Entry',
        default='yes',
        widget_type='checkbutton',
    ),
    Setting(
        section="general",
        key="unit",
        label="Pressure units",
        default="Torr",
        widget_type='combobox'
    ),

    # --------------------
    # [report.header]
    # --------------------
    Setting(
        section="report.header",
        key="company",
        label="Company Name",
        report_cell='B3',
    ),
    Setting(
        section="report.header",
        key="project",
        label="Project Name",
        report_cell='B4',
    ),
    Setting(
        section="report.header",
        key="service_number",
        label="Service Number",
        report_cell='B5',
    ),
    Setting(
        section="report.header",
        key="machine",
        label="Machine Name",
        report_cell='B6',
    ),
    Setting(
        section="report.header",
        key="location",
        label="Location",
        report_cell='B7',
    ),
    Setting(
        section="report.header",
        key="date",
        label="Date",
        report_cell='F2',
    ),
    Setting(
        section="report.header",
        key="calibration_type",
        label="Calibration Type",
        report_cell = 'F5',
    ),
    Setting(
        section="report.header",
        key="procedure",
        label="Procedure",
        report_cell='F6',
    ),
    Setting(
        section="report.header",
        key="calibration",
        label="Calibration",
        report_cell='F7',
    ),

    # --------------------
    # [report.device]
    # --------------------
    Setting(
        section="report.device",
        key="dev_manufacturer",
        label="Manufacturer",
        report_cell='C10',
    ),
    Setting(
        section="report.device",
        key="dev_model_number",
        label="Model Number",
        report_cell='C11',
    ),
    Setting(
        section="report.device",
        key="dev_serial_number",
        label="Serial Number",
        report_cell='C12',
    ),
    Setting(
        section="report.device",
        key="dev_tag_id_number",
        label="Tag/ID Number",
        report_cell='C13',
    ),
    Setting(
        section="report.device",
        key="dev_range",
        label="Range",
        report_cell='C14',
    ),
    Setting(
        section="report.device",
        key="dev_device_accuracy",
        label="Device Accuracy",
        report_cell='C15',
    ),
    Setting(
        section="report.device",
        key="dev_output_signal",
        label="Output Signal",
        report_cell='C16',
    ),

    # --------------------
    # [report.standard]
    # --------------------
    Setting( # Sets the default standard transducer (i.e. the one on the cal cart)
        section='report.standard',
        key='preset',
        label='Standard Preset',
        default='<select>',
        widget_type='combobox'
    ),
    Setting(
        section='report.standard',
        key='std_manufacturer',
        label='Manufacturer',
        report_cell='G10',
    ),
    Setting(
        section='report.standard',
        key='std_model_number',
        label='Model Number',
        report_cell='G11',
    ),
    Setting(
        section='report.standard',
        key='std_serial_number',
        label='Serial Number',
        report_cell='G12',
    ),
    Setting(
        section="report.standard",
        key="std_calibration_date",
        label="Calibration Date",
        report_cell='G13',

    ),
    Setting(
        section="report.standard",
        key="std_calibration_due_date",
        label="Calibration Due Date",
        report_cell='G14',
    ),
    Setting(
        section="report.standard",
        key="std_standard_accuracy",
        label="Standard Accuracy",
        report_cell='G15',
    ),
    Setting(
        section="report.standard",
        key="std_accuracy_ratio",
        label="Accuracy Ratio",
        report_cell='G16',
    ),

    # --------------------
    # [setpoint.i]
    # --------------------
    Setting(
        section="setpoint",
        key="pressure",
        label="Setpoint pressure",
        default="0.1",
    ),
    Setting(
        section="setpoint",
        key="max_err",
        label="Setpoint error tolerance",
        default="0.005",
    ),
]

SETTINGS_BY_KEY = {
    s.key: s
    for s in SETTINGS
}