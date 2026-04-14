# Import necessary packages
import csv
from datetime import datetime
import time
from pymeasure.instruments.keithley import Keithley2450
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from time import sleep
from pymeasure.display import Plotter
# from PyQt5 import QtWidgets, uic, QtGui
from matplotlib.animation import FuncAnimation
# plt.style.use('fivethirtyeight')

# Set the input parameters
data_points = 30
max_voltage = 3
min_voltage = -0.1

# Connect and configure the instrument
# ipaddr = "TCPIP0::169.254.144.151::inst0::INSTR" #SMU1
# ipaddr = "TCPIP0::169.254.159.59::inst0::INSTR" #SMU2

ipaddr = "TCPIP0::134.157.105.90::inst0::INSTR"
# ipaddr = "TCPIP0::134.157.105.94::inst0::INSTR"

sourcemeter = Keithley2450(ipaddr)  
# print(sourcemeter.id)
# print(sourcemeter.ask('*IDN?'))
sourcemeter.reset()
sourcemeter.use_front_terminals()
#sourcemeter.measure_concurent_functions
# sourcemeter.measure_current()
sourcemeter.apply_voltage()
sourcemeter.source_voltage = min_voltage  # Sets the source voltage to min voltage
sourcemeter.enable_source()
sleep(0.1) # wait here to give the instrument time to react

# Allocate arrays to store the measurement results
voltages = np.linspace(min_voltage, max_voltage, num=data_points)
currents = np.zeros_like(voltages)
resistances = np.zeros_like(voltages)
voltage_stds = np.zeros_like(voltages)
sleep(0.1)

# Save the data columns in a CSV file
now = datetime.now()
headers = ['Timestamp', "Data point", 'I', 'V']
with open('data.csv', 'w', newline='') as csv_file:
    csv_writer = csv.DictWriter(csv_file, lineterminator='\n', fieldnames=headers)
    csv_writer.writeheader()
num_row = 0
while num_row <= data_points-1:
    Timestamp = now
    # sourcemeter.start_buffer()
    sleep(0.1)
    sourcemeter.source_voltage = voltages[num_row]
    sleep(0.1)
    sourcemeter.measure_current()
    sleep(0.1)
    currents[num_row] = sourcemeter.current
    
    with open('data.csv', 'a') as csv_file:
        csv_writer = csv.DictWriter(csv_file, lineterminator='\n', fieldnames=headers)
        data = {
                "Timestamp": Timestamp,
                "Data point" : num_row,
                "I": currents[num_row],
                "V": voltages[num_row],
                }
        csv_writer.writerow(data)
    print(headers)
    print(Timestamp, num_row, currents[num_row], voltages[num_row])
    num_row +=1
    time.sleep(1)
    
sourcemeter.shutdown()

