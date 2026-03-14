import csv
import time
import logging
import os
import multiprocessing as mp
import instrument_setting
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from pymeasure.instruments.keithley import Keithley2450
from queue import Empty

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
from pymeasure.log import console_log
console_log(log)

class CreateFile():
    def __init__(self, procedure):
        self.procedure = procedure  # Get the procedure name.
        self.createfile()           # Call create file function.

    def createfile(self):
        date = datetime.now().date()                                        # Assign today's date into date.
        PARENT_DIR = "D:/Sorbonne University 2009 - present/2024 - 2025/ANA2/SMU codes/MOS_IV_v6/{}/".format(date)   # Get the path. #!!!!CHANGE DIRECTORY!!!!#
        DIR = '{}'.format(self.procedure)                                   # Get procedure name.
        self.PATH = os.path.join(PARENT_DIR, DIR)                           # Form a full path.
        try:
            if not os.path.exists(self.PATH):                               # If the given path does not exists.
                os.makedirs(self.PATH)                                      # Make a directory.
        except OSError:                                                     # OSError occur, don't make the directory.
            print ("Creation of the directory [%s] failed." % DIR)          # Print message.
        #else:                                                              # Successfully created the directory, print the message.
            #print ("Successfully created the directory %s " % DIR)

    def get_file(self):
        file_list = os.listdir(self.PATH)   # Load path into list directory.
        file_count = len(file_list)         # Chech the number of file(s) under the given path.
        return [self.PATH, file_count]      # Return full path and file count under this folder.

class IV_Characteristic(mp.Process):
    def __init__(self, file_name, queue, measurement_type):
        super().__init__()
        self.file_name = file_name
        self.queue = queue
        self.measurement_type = measurement_type
        
        #Extract parameters for SMU1 (Gate)
        # self.gate_control = instrument_setting.GATE_CONTROL
        self.minimum_gate_voltage = instrument_setting.GATEVOLTAGE_MIN
        self.maximum_gate_voltage = instrument_setting.GATEVOLTAGE_MAX
        self.gate_voltage_step = instrument_setting.GATEVOLTAGE_STEP
        #Extract parameters for SMU2 (Drain)
        # self.drain_control = instrument_setting.DRAIN_CONTROL
        self.minimum_drain_voltage = instrument_setting.DRAINVOLTAGE_MIN
        self.maximum_drain_voltage = instrument_setting.DRAINVOLTAGE_MAX
        self.drain_voltage_step = instrument_setting.DRAINVOLTAGE_STEP
        
    def init_keithley(self):
        print("Initialize Instrument(s)...")

        # ipaddr_1 = "TCPIP0::169.254.191.190::inst0::INSTR" #SMU1 (Gate)
        # ipaddr_2 = "TCPIP0::169.254.22.41::inst0::INSTR" #SMU2 (Drain)

        ipaddr_1 = "TCPIP0::134.157.105.90::inst0::INSTR" #SMU1 (Gate)
        ipaddr_2 = "TCPIP0::134.157.105.94::inst0::INSTR" #SMU2 (Drain)
        
        self.sourcemeter_1 = Keithley2450(ipaddr_1)
        self.sourcemeter_2 = Keithley2450(ipaddr_2)
        
        self.sourcemeter_1.apply_voltage() #Mode voltage source
        self.sourcemeter_2.apply_voltage()
        
        self.sourcemeter_2.measure_current() #Mode measure current
        
        self.sourcemeter_1.use_front_terminals()
        self.sourcemeter_2.use_front_terminals()
        
        self.sourcemeter_1.compliance_current = instrument_setting.CURRENT_COMPLIANCE
        self.sourcemeter_2.compliance_current = instrument_setting.CURRENT_COMPLIANCE
        
    def record_csv(self, fileName, now, Vg, Vd, Id):
        with open(fileName, 'a', newline='') as csvfile:
            header = ["Timestamp", "Gate_Voltage","Drain_Voltage", "Drain_Current"]
            writer = csv.DictWriter(csvfile, fieldnames=header)
            if csvfile.tell() == 0:
                writer.writeheader()
            writer.writerow(
                {
                    "Timestamp": now,
                    "Gate_Voltage": Vg,
                    "Drain_Voltage": Vd,
                    "Drain_Current": Id
                }
            )
        csvfile.close()

    def IdVg_Measurement(self):
        file_name = "".join([self.file_name, "/IdVg"])
        file_path = CreateFile(file_name).get_file()
        fileName = "{}/{}_{}.csv".format(file_path[0], "IdVg", file_path[1])
        
        self.init_keithley()
        time.sleep(1)
        
        log.info("Measurement with gate control ON from {} V to {} V with {} V step".format(self.minimum_gate_voltage, 
                                                                                            self.maximum_gate_voltage, 
                                                                                            self.gate_voltage_step))
        
        self.sourcemeter_1.source_voltage = self.minimum_gate_voltage #Apply gate voltage
        self.sourcemeter_1.enable_source()
        
        self.sourcemeter_2.source_voltage = self.minimum_drain_voltage #Apply fixed drain voltage
        self.sourcemeter_2.enable_source()
        time.sleep(5) #Stabilize readings

        for Vd in np.arange(self.minimum_drain_voltage, self.maximum_drain_voltage + self.drain_voltage_step, self.drain_voltage_step):
            self.sourcemeter_2.source_voltage = Vd #Apply drain voltage
            time.sleep(1) #Stabilize readings
            
            for Vg in np.arange(self.minimum_gate_voltage, self.maximum_gate_voltage + self.gate_voltage_step, self.gate_voltage_step):
                self.sourcemeter_1.source_voltage = Vg  #Apply gate voltage
                time.sleep(1)  # Stabilise
                
                now = datetime.now().time()
                Id = self.sourcemeter_2.current #Measure drain current

                log.info("Measurement at Vg = {} V, Vd = {} V, Id = {} A".format(Vg, Vd, Id))
                self.record_csv(fileName, now, Vg, Vd, Id)
                
                # Send data to the queue
                self.queue.put((Vg, Id, Vd))
                
        self.sourcemeter_1.disable_source()
        self.sourcemeter_2.disable_source()
              
    def IdVd_Measurement(self):
        file_name = "".join([self.file_name, "/IdVd"])
        file_path = CreateFile(file_name).get_file()
        fileName = "{}/{}_{}.csv".format(file_path[0], "IdVd", file_path[1])
        
        self.init_keithley()
        time.sleep(1)
        
        log.info("Measurement with gate control ON from {} V to {} V with {} V step".format(self.minimum_gate_voltage, 
                                                                                            self.maximum_gate_voltage, 
                                                                                            self.gate_voltage_step))
        
        self.sourcemeter_1.source_voltage = self.minimum_gate_voltage #Apply gate voltage
        self.sourcemeter_1.enable_source()
        
        self.sourcemeter_2.source_voltage = self.minimum_drain_voltage #Apply drain voltage
        self.sourcemeter_2.enable_source()
        time.sleep(5) #Stabilize readings
        
        for Vg in np.arange(self.minimum_gate_voltage, self.maximum_gate_voltage + self.gate_voltage_step, self.gate_voltage_step):
            self.sourcemeter_1.source_voltage = Vg #Apply gate voltage
            time.sleep(1)  # Stabilise
            
            for Vd in np.arange(self.minimum_drain_voltage, self.maximum_drain_voltage + self.drain_voltage_step, self.drain_voltage_step):
                self.sourcemeter_2.source_voltage = Vd #Apply drain voltage
                time.sleep(1) #Stabilize readings

                now = datetime.now().time()
                Id = self.sourcemeter_2.current #store drain current

                log.info("Measurement at Vg = {} V, Vd = {} V, Id = {} A".format(Vg, Vd, Id))
                self.record_csv(fileName, now, Vg, Vd, Id)
                
                # Send data to the queue
                self.queue.put((Vd, Id, Vg))
                
        self.sourcemeter_1.disable_source()
        self.sourcemeter_2.disable_source()
        
    def run(self):
        if self.measurement_type == "IdVg":
            self.IdVg_Measurement()
            
        elif self.measurement_type == "IdVd":
            self.IdVd_Measurement()

def plot_live(queue, colormap, x_label, y_label, legend_label):
    fig, ax = plt.subplots()
    ax.set_title("Live Measurement")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)

    lines = {}
    
    while True:
        try:
            x, y, z = queue.get(timeout=0.1)
            if z not in lines:
                color = colormap(len(lines) / 10)
                lines[z], = ax.plot([], [], 'o-', label=f"{legend_label} = {z} V", color=color)

            line = lines[z]
            xdata, ydata = line.get_data()
            xdata = np.append(xdata, x)
            ydata = np.append(ydata, y)
            line.set_data(xdata, ydata)

            ax.relim()
            ax.autoscale_view()
            ax.legend()
            plt.pause(0.01)
        except Empty:
            pass   
            
if __name__ == "__main__":
    queue = mp.Queue()
    colormap = cm.get_cmap("viridis")

    # Choose the measurement type
    # measurement_type = "IdVg"  # Change to "IdVd" for IdVd measurement,
                               #           "IdVg" for IdVg measurement.
    measurement_type = "IdVd"  # Change to "IdVd" for IdVd measurement,


    # Start the measurement process
    measurement_process = IV_Characteristic("IV_Characteristic", queue, measurement_type)
    measurement_process.start()

    # Start live plotting
    if measurement_type == "IdVg":
        plot_live(queue, colormap, "Gate Voltage (V)", "Drain Current (A)", "Vd")
    elif measurement_type == "IdVd":
        plot_live(queue, colormap, "Drain Voltage (V)", "Drain Current (A)", "Vg")

    measurement_process.join()



