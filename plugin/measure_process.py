import logging
import math
from multiprocessing import Event, Process
from multiprocessing.connection import Connection
import pickle

import numpy as np
from auto_detect import get_cpu_info
import time
import pandas as pd
import psutil

logger = logging.getLogger(__name__)


class MeasureProcess(Process):
    def __init__(self, connection: Connection, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.daemon = True
        self.exit = Event()
        self.connection = connection

    def run(self):
        now = time.time_ns()

        cpu_info = get_cpu_info(logger)

        Z = pd.DataFrame.from_dict({
            'HW_CPUFreq': [cpu_info['cpu-freq']],
            'CPUThreads': [cpu_info['cpu-threads']],
            'CPUCores': [cpu_info['cpu-cores']],
            # 'TDP': [cpu_info['tdp']],
            'TDP': [105],
            'HW_MemAmountGB': [cpu_info['ram']],
            # 'Architecture': [cpu_info['architecture']],
            'Architecture': ['epyc-gen3'],  # Ryzen not supported
            'CPUMake': [cpu_info['cpu-make']],
            'utilization': [0.0]
        })

        Z = pd.get_dummies(Z, columns=['CPUMake', 'Architecture'])
        Z = Z.dropna(axis=1)

        model = pickle.load(open('model.pkl', 'rb'))

        predictions = {}
        cpu_temps = []
        this_process = psutil.Process()
        parent_process = this_process.parent()
        while not self.exit.is_set():
            utilization = parent_process.cpu_percent(
                interval=0.1) / psutil.cpu_count()
            if utilization == 0 or utilization > 100:
                continue
            Z['utilization'] = float(utilization)
            predictions[time.time()] = model.predict(Z)[0]
            cpu_temps.append(psutil.sensors_temperatures())
            time.sleep(0.2)

        total_time = time.time_ns() - now
        total_time_ms = math.ceil(total_time / 1_000_000)

        energy = 0
        last_time = 0
        for key in predictions:
            if last_time != 0:
                energy += predictions[key] * (key - last_time)
                last_time = key
            else:
                last_time = key

        self.connection.send((total_time_ms, energy, float(np.mean(
            list(predictions.values())))))

    def terminate(self):
        self.exit.set()
