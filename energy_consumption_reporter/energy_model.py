
import logging
import os
import pandas as pd
import pickle
from xgboost import XGBRegressor

from energy_consumption_reporter.auto_detect import get_cpu_info
from energy_consumption_reporter.singleton import SingletonMeta

logger = logging.getLogger(__name__)

file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))
model_path = os.path.join(file_dir, 'model.pkl')
data_path = os.path.join(file_dir, 'data/spec_data_cleaned.csv')


class EnergyModel(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.cpu_info = get_cpu_info(logger)

        self.Z = pd.DataFrame.from_dict({
            'HW_CPUFreq': [self.cpu_info.freq],
            'CPUThreads': [self.cpu_info.threads],
            'CPUCores': [self.cpu_info.cores],
            'TDP': [self.cpu_info.tdp or 100],
            'HW_MemAmountGB': [self.cpu_info.mem],
            'Architecture': [self.cpu_info.architecture],
            'CPUMake': [self.cpu_info.make],
            'utilization': [0.0]
        })

        self.Z = pd.get_dummies(self.Z, columns=['CPUMake', 'Architecture'])
        self.Z = self.Z.dropna(axis=1)
        if os.path.exists(model_path):
            self.model = pickle.load(open(model_path, 'rb'))
        else:
            self.train_model()
        self.is_setup = True

    def predict(self, utilization: float):
        if not self.is_setup:
            raise Exception("Model not setup")

        self.Z['utilization'] = utilization
        predicion = self.model.predict(self.Z)[0]
        return predicion

    def train_model(self, export=True):
        cpu_chips = self.cpu_info.chips

        logger.info('Training model')
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

        X = X[self.Z.columns]

        logger.info(
            'Model will be trained on the following columns and restrictions: \n%s', self.Z)

        self.model = XGBRegressor()
        self.model.fit(X, y)
        if export:
            pickle.dump(self.model, open(model_path, "wb"))
