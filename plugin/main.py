import os
import pickle
import pandas as pd
from xgboost import XGBRegressor
from auto_detect import get_cpu_info
import logging
from functools import lru_cache, wraps

from measure_process import MeasureProcess


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def train_model(cpu_chips, Z):

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


def create_model():
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
    model = train_model(cpu_info['cpu-chips'], Z)
    pickle.dump(model, open('model.pkl', "wb"))


def energy_test(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):
        if not os.path.exists(os.getcwd() + '/model.pkl'):
            create_model()

        process = MeasureProcess()
        process.start()

        func()

        process.terminate()
        process.join()

    return wrapper_func


@energy_test
def test_func():
    def fib(n):
        if n <= 1:
            return n
        else:
            return fib(n-1) + fib(n-2)

    fib(40)


if __name__ == '__main__':
    test_func()
