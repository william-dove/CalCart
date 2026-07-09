#calibration/report.py
import xlwings as xw

def generate_report(results, resultspath):
    '''
    Makes a PDF report after running a calibration sequence from the GUI.
    '''
    