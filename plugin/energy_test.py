from multiprocessing import Pipe
import os
import pickle
import pandas as pd
from xgboost import XGBRegressor
from .auto_detect import get_cpu_info
import logging
from functools import wraps

from .measure_process import MeasureProcess
from .singleton import SingletonMeta
from .report_builder import ReportBuilder

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))

class EnergyTest(metaclass=SingletonMeta):
    def __init__(self, func_name="") -> None:
        self.conn1, self.conn2 = Pipe()
        self.process = None

        self.func_name = func_name

        # self.report_builder = ReportBuilder(
        #     name="CPU Performance Report"
        # )
        # self.report_builder.generate_report()

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop(exc_type, exc_value, traceback)
        self.report_builder.save_report()

    def train_model(self, cpu_chips, Z):
        data_path = os.path.join(file_dir, 'data/spec_data_cleaned.csv')
        df = pd.read_csv(data_path)

        X = df.copy()
        X = pd.get_dummies(X, columns=['CPUMake', 'Architecture'])

        if cpu_chips:
            logger.info(
                'Training data will be restricted to the following amount of chips: %d', cpu_chips)

            X = X[X.CPUChips == cpu_chips]

        if X.empty:
            raise RuntimeError(
                f"The training data does not contain any servers with a chips amount ({cpu_chips}). Please select a different amount.")

        y = X.power

        X = X[Z.columns]

        logger.info(
            'Model will be trained on the following columns and restrictions: \n%s', Z)

        model = XGBRegressor()
        model.fit(X, y)

        return model

    def create_model(self):
        cpu_info = get_cpu_info(logger)

        Z = pd.DataFrame.from_dict({
            'HW_CPUFreq': [cpu_info.freq],
            'CPUThreads': [cpu_info.threads],
            'CPUCores': [cpu_info.cores],
            'TDP': [cpu_info.tdp],
            'HW_MemAmountGB': [cpu_info.mem],
            'Architecture': [cpu_info.architecture],
            'CPUMake': [cpu_info.make],
            'utilization': [0.0]
        })

        Z = pd.get_dummies(Z, columns=['CPUMake', 'Architecture'])
        Z = Z.dropna(axis=1)

        logger.info('Training model')
        model = self.train_model(cpu_info.chips, Z)
        pickle.dump(model, open('model.pkl', "wb"))

    @staticmethod
    def energy_test(times=1):
        def decorate(func):
            @wraps(func)
            def wrapper_func(*args, **kwargs):
                EnergyTest().test(func, times)

            return wrapper_func
        return decorate

    def test(self, func, times):
        if not os.path.exists( os.path.join(file_dir, '/model.pkl')):
            self.create_model()

        conn1, conn2 = Pipe()

        energy_list = []
        power_list = []
        time_list = []
        passed = True
        counter = 0
        stop = False
        while counter < times and not stop:
            logging.debug(
                f"Running test {func.__name__} for the {counter+1} time")
            process = MeasureProcess(conn1)
            process.start()
            reason = ""

            try:
                func()
            except AssertionError as e:
                reason = str(e)
                passed = False
                stop = True

            process.terminate()
            logging.debug(
                f"Done, waiting for values")
            logging.debug(process.exit)

            values = conn2.recv()
            if isinstance(values, Exception):
                raise values
            time_list.append(values[0])
            energy_list.append(values[1])
            power_list.append(values[2])
            process.join()

            counter += 1

        # self.report_builder.add_case(time_list=time_list,
        #                              energy_list=energy_list,
        #                              power_list=power_list,
        #                              test_name=func.__name__,
        #                              passed=passed,
        #                              reason=reason)

        # self.report_builder.save_report()
        return {"time": time_list, "energy": energy_list, "power": power_list}

    def start(self):
        self.process = MeasureProcess(self.conn1)
        self.process.start()

    def stop(self, exc_type, exc_value, traceback):
        if self.process is None:
            return

        self.process.terminate()
        self.process.join()

        energy_list = []
        power_list = []
        time_list = []
        values = self.conn2.recv()
        time_list.append(values[0])
        energy_list.append(values[1])
        power_list.append(values[2])

        self.report_builder.add_case(time_list=time_list,
                                     energy_list=energy_list,
                                     power_list=power_list,
                                     test_name=self.func_name,
                                     passed=True if exc_type is None else False,
                                     reason=str(exc_value) if exc_value is not None else "")
