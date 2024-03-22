import math
from multiprocessing import Event, Process
from multiprocessing.connection import Connection

from  .energy_model import EnergyModel
import time
import psutil
import numpy as np
class MeasureProcess(Process):
    def __init__(self, connection: Connection, model: EnergyModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.daemon = True
        self.exit = Event()
        self.model = model
        self.connection = connection

    def run(self):
        try:
            now = time.time_ns()
            
            if self.model is None or not self.model.is_setup:
                raise Exception("Model not setup!")

            # measurements
            measurements: list[tuple[int, float]] = []
            cpu_temps = []
            
            # get parent process
            this_process = psutil.Process()
            parent_process = this_process.parent()
            
            while not self.exit.is_set():
                utilization = parent_process.cpu_percent(
                    interval=0.1) / psutil.cpu_count()
                if utilization == 0 or utilization > 100:
                    continue
                
                now = time.time_ns()
                wattage = self.model.predict(float(utilization))
                measurement = (now, wattage)
                measurements.append(measurement)
                try:
                    cpu_temps.append(psutil.sensors_temperatures())
                except:
                    pass
                time.sleep(0.2)

            total_time = time.time_ns() - now
            total_time_ms = math.ceil(total_time / 1_000_000)

            # convert measurements (W) to energy (J)
            energy = 0
            last_time = 0
            for (t, wattage) in measurements:
                if last_time == 0:
                    last_time = t
                else:
                    delta_t = t - last_time
                    energy += wattage * delta_t
                    last_time = t

            # get average wattage
            wattages = [x[1] for x in measurements]
            avg_wattage = float(np.mean(
                list(wattages)))

            self.connection.send((total_time_ms, energy, avg_wattage))
        except Exception as e:
            self.connection.send(e)

    def terminate(self):
        self.exit.set()
