# Import necessary packages
from pymeasure.instruments.keithley import Keithley2400
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from time import sleep
from pymeasure.display import Plotter
# from PyQt5 import QtWidgets, uic, QtGui
from matplotlib.animation import FuncAnimation
plt.style.use('fivethirtyeight')

x_values = []
y_values = []

def animate(i):
        plt.cla()
        data = pd.read_csv("data.csv")
        x_values = data["V"]
        y_values = abs(data["I"])
        plt.plot(x_values, y_values)
        plt.xlabel('Voltage (V)')
        plt.ylabel('Current (A)')
        # plt.yscale('log')
        plt.title('I-V')
  
ani = FuncAnimation(plt.gcf(), animate, 1000)
plt.gcf().autofmt_xdate()
plt.tight_layout()
plt.show()
