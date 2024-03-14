import os
import pickle
import threading
import time
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from auto_detect import get_cpu_info
import logging
from time import sleep
import psutil

from report_builder import ReportBuilder


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

running = True


def train_model(cpu_chips, Z):

    df = pd.read_csv(
        os.getcwd() + '/plugin/spec_power_model/data/spec_data_cleaned.csv')

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

    X = X[Z.columns]  # only select the supplied columns from the command line

    logger.info(
        'Model will be trained on the following columns and restrictions: \n%s', Z)

#    params = {
#      'max_depth': 10,
#      'learning_rate': 0.3037182109676833,
#      'n_estimators': 792,
#      'min_child_weight': 1,
#      'random_state': 762
#    }
    params = {}

    model = XGBRegressor(**params)
    model.fit(X, y)

    return model


def start_measurement(pid: int):
    global running

    now = time.time()

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

    model: XGBRegressor
    if not os.path.exists(os.getcwd() + '/model.pkl'):
        logger.info('Training model')
        model = train_model(cpu_info['cpu-chips'], Z)
        pickle.dump(model, open('model.pkl', "wb"))
    else:
        logger.info('Loading model')
        model = pickle.load(open('model.pkl', 'rb'))

    process = psutil.Process(pid)
    predictions = {}
    cpu_temps = []
    while (running):
        utilization = process.cpu_percent()
        print("Utilization: ", utilization)
        Z['utilization'] = float(utilization)
        predictions[time.time()] = model.predict(Z)[0]
        cpu_temps.append(psutil.sensors_temperatures())
        time.sleep(0.2)

    total_time = time.time() - now
    print("Time: ", total_time)

    print("Predictions: ", predictions)

    # calculate energy consumption over prediction which is in Watts
    energy = 0
    last_time = 0
    for key in predictions:
        if last_time != 0:
            energy += predictions[key] * (key - last_time)
            last_time = key
        else:
            last_time = key

    print("Energy: ", energy)

    report_builder = ReportBuilder(cpu_info, total_time, energy, float(np.mean(
        list(predictions.values()))), "CPU Performance Report")
    report_builder.generate_report()
    report_builder.print_report()
    report_builder.save_report('report.json')

    # predictions = pd.DataFrame.from_dict(predictions, orient='index')
    # predictions.to_csv('predictions.csv', index=False)


def stop_measurement():
    global running
    running = False
    return 'Measurement stopped'


if __name__ == '__main__':
    pid = os.getpid()

    thread = threading.Thread(target=start_measurement, args=(pid,))
    thread.start()

    sleep(5)

    stop_measurement()

    thread.join()
