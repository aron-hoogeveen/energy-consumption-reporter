from multiprocessing import Pipe
import os
import pickle
import pandas as pd
from xgboost import XGBRegressor
from auto_detect import get_cpu_info
import logging
from functools import wraps

from measure_process import MeasureProcess
from singleton import SingletonMeta
from report_builder import ReportBuilder


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


class EnergyTest(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.report_builder = ReportBuilder(
            name="CPU Performance Report"
        )
        self.report_builder.generate_report()

    def train_model(self, cpu_chips, Z):

        df = pd.read_csv(
            os.getcwd() + '/plugin/data/spec_data_cleaned.csv')

        X = df.copy()
        X = pd.get_dummies(X, columns=['CPUMake', 'Architecture'])

        if cpu_chips:
            logger.info(
                'Training data will be restricted to the following amount of chips: %d', cpu_chips)

            # Fit a model for every amount of CPUChips
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

        logger.info('Training model')
        model = self.train_model(cpu_info['cpu-chips'], Z)
        pickle.dump(model, open('model.pkl', "wb"))

    @staticmethod
    def energy_test(times=1):
        def decorate(func):
            @wraps(func)
            def wrapper_func(*args, **kwargs):
                EnergyTest().test(func=func, times=times)

            return wrapper_func
        return decorate

    def test(self, func, times=1):
        if not os.path.exists(os.getcwd() + '/model.pkl'):
            self.create_model()

        conn1, conn2 = Pipe()

        energy_list = []
        power_list = []
        time_list = []
        passed = True
        counter = 0
        stop = False
        while counter < times and not stop:
            print(f"Running test {func.__name__} for the {counter+1} time")
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
            process.join()

            values = conn2.recv()
            time_list.append(values[0])
            energy_list.append(values[1])
            power_list.append(values[2])

            counter += 1

        self.report_builder.add_case(time_list=time_list,
                                     energy_list=energy_list,
                                     power_list=power_list,
                                     test_name=func.__name__,
                                     passed=passed,
                                     reason=reason)

        self.report_builder.save_report(os.getcwd() + '/report.json')
