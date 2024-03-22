
import logging
import os
import pandas as pd
import pickle
from xgboost import XGBRegressor

from .auto_detect import CPUInfo, get_cpu_info
from .singleton import SingletonMeta

logger = logging.getLogger(__name__)

file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))
model_path = os.path.join(file_dir, 'model.pkl')
data_path = os.path.join(file_dir, 'data/spec_data_cleaned.csv')

class EnergyModel(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.model = None
        self.Z = None
        self.is_setup = False
        self.cpu_info: CPUInfo = None
    
    def setup(self):
        cpu_info = get_cpu_info(logger)
        self.cpu_info = cpu_info

        self.Z = pd.DataFrame.from_dict({
            'HW_CPUFreq': [cpu_info.freq],
            'CPUThreads': [cpu_info.threads],
            'CPUCores': [cpu_info.cores],
            'TDP': [cpu_info.tdp or 100],
            'HW_MemAmountGB': [cpu_info.mem],
            'Architecture': [cpu_info.architecture or "epyc-gen3"],
            'CPUMake': [cpu_info.make],
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
        return self.model.predict(self.Z)[0]
    
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
            pickle.dump(self.model, open('model.pkl', "wb"))
