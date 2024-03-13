import os
import pickle
import threading
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from auto_detect import get_cpu_info
import logging
from time import sleep
import psutil


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


def interpolate_helper(predictions, lower, upper, step=501):

    diff = int(upper-lower)
    diff_value = predictions[upper] - predictions[lower]

    for i in np.linspace(0, diff, step):
        predictions[round(lower+i, 2)] = predictions[lower] + \
            ((diff_value/diff)*i)

    return predictions


def interpolate_predictions(predictions):
    predictions = interpolate_helper(predictions, 0.0, 5.0, 501)
    predictions = interpolate_helper(predictions, 5.0, 15.0, 1001)
    predictions = interpolate_helper(predictions, 15.0, 25.0, 1001)
    predictions = interpolate_helper(predictions, 25.0, 35.0, 1001)
    predictions = interpolate_helper(predictions, 35.0, 45.0, 1001)
    predictions = interpolate_helper(predictions, 45.0, 55.0, 1001)
    predictions = interpolate_helper(predictions, 55.0, 65.0, 1001)
    predictions = interpolate_helper(predictions, 65.0, 75.0, 1001)
    predictions = interpolate_helper(predictions, 75.0, 85.0, 1001)
    predictions = interpolate_helper(predictions, 85.0, 95.0, 1001)
    # Question: between 95 and 100 is no difference. How do we extrapolate?
    predictions = interpolate_helper(predictions, 95.0, 100.0, 501)

    return predictions


def start_measurement(pid: int):
    global running

    cpu_info = get_cpu_info(logger)

    Z = pd.DataFrame.from_dict({
        'HW_CPUFreq': [cpu_info['cpu-freq']],
        'CPUThreads': [cpu_info['cpu-threads']],
        'CPUCores': [cpu_info['cpu-cores']],
        'TDP': [cpu_info['tdp']],
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
    counter = 0
    while (running):
        utilization = process.cpu_percent()
        print("Utilization: ", utilization)
        Z['utilization'] = float(utilization)
        predictions[counter] = model.predict(Z)[0]
        print("Prediction: ", predictions[counter])
        counter += 1
        sleep(1)

    predictions = pd.DataFrame.from_dict(predictions, orient='index')
    predictions.to_csv('predictions.csv', index=False)


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
