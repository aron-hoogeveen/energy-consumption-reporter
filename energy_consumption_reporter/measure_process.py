import json
import math
from multiprocessing import Event, Process
import subprocess
try:
    import wmi
except ImportError:
    pass
import time
import psutil
import numpy as np


class MeasureProcess(Process):
    def __init__(self, connection, model, *args, **kwargs):
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

                if utilization < 0 or utilization > 100:
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
                        if len(thermal_zone_info) > 0:
                            cpu_temp = int(thermal_zone_info[0].Temperature - 273.15)
                            cpu_temps.append(cpu_temp)
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
            wattages = [x[1] for x in measurements]
            # get average wattage
            times = [x[0] / 1_000_000_000 for x in measurements]
            energy = np.trapz(wattages, times)
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
