import json
import math
from multiprocessing import Event, Process
from multiprocessing.connection import Connection, PipeConnection
import os
import subprocess
import wmi
import time
import psutil
import numpy as np


class MeasureProcess(Process):
    def __init__(self, connection: Connection | PipeConnection, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.daemon = True
        self.exit = Event()
        self.connection = connection
        self.model = model

    def run(self):
        try:
            if self.model is None:
                raise Exception("Model not setup!")

            # measurements
            start = time.time_ns()
            measurements: list[tuple[int, float]] = []
            cpu_temps = []

            # get parent process
            this_process = psutil.Process()
            parent_process = this_process.parent()

            while not self.exit.is_set():
                # measure the next 0.2 seconds
                utilization = parent_process.cpu_percent(
                    interval=0.2) / psutil.cpu_count()

                if utilization == 0 or utilization > 100:
                    continue

                now = time.time_ns()
                wattage: float = self.model.predict(float(utilization))
                measurement = (now, wattage)
                measurements.append(measurement)

                try:
                    if psutil.WINDOWS:
                        c = wmi.WMI()
                        thermal_zone_info = c.query(
                            "SELECT * FROM Win32_PerfFormattedData_Counters_ThermalZoneInformation WHERE Name LIKE '%CPU%'")
                        cpu_temps.append(
                            int(thermal_zone_info[0].Temperature - 273.15))
                    else:
                        sensor_data = json.loads(subprocess.check_output(
                            ["sensors", "-j"]).decode("utf-8"))
                        cpu_temps.append(int(sensor_data.get(
                            "k10temp-pci-00c3").get("Tctl").get("temp1_input")))
                except:
                    pass

            if len(measurements) == 0:
                raise Exception(
                    "No measurements were taken\n Function probably ran too fast or was interrupted.")

            total_time = time.time_ns() - start
            total_time_ms = math.ceil(total_time / 1_000_000)

            # convert measurements (W) to energy (J)
            energy = 0
            last_time = start
            for (t, wattage) in measurements:
                delta_t = t - last_time
                delta_t_s = delta_t / 1_000_000_000
                energy += wattage * delta_t_s
                last_time = t

            # get average wattage
            wattages = [x[1] for x in measurements]
            avg_wattage = float(np.mean(
                list(wattages)))
            avg_temp = float(np.mean(
                list(cpu_temps)))

            self.connection.send(
                (total_time_ms, energy, avg_wattage, avg_temp))
        except Exception as e:
            self.connection.send(e)

    def terminate(self):
        self.exit.set()
