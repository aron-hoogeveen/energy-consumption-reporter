from multiprocessing import Pipe
import os

from .energy_model import EnergyModel
import logging
from functools import wraps

from .measure_process import MeasureProcess
from .singleton import SingletonMeta
from .report_builder import ReportBuilder

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


class EnergyTest(metaclass=SingletonMeta):

    def __init__(self, test_id="", energy_model: EnergyModel = None) -> None:
        self.conn1, self.conn2 = Pipe()
        self.process = None

        self.test_id = test_id
        self.energy_model = energy_model

        # self.report_builder = ReportBuilder(
        #     name="CPU Performance Report"
        # )
        # self.report_builder.generate_report()

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop(exc_type, exc_value, traceback)
        # self.report_builder.save_report()

    @staticmethod
    def energy_test(times=1):
        def decorate(func):
            @wraps(func)
            def wrapper_func(*args, **kwargs):
                EnergyTest().test(func, times)

            return wrapper_func
        return decorate

    def test(self, func, times):
        if self.energy_model is None or not self.energy_model.is_setup:
            raise Exception("Must provide a trained model")

        conn1, conn2 = Pipe()

        energy_list = []
        power_list = []
        time_list = []
        passed = True

        for i in range(times):
            nth = i + 1
            logging.debug(f"Test {self.test_id}, Iteration: {nth}")
            process = MeasureProcess(conn1, self.energy_model)
            process.start()
            reason = ""

            logging.debug(
                f"Running method {func.__name__}...")
            try:
                func()
            except AssertionError as e:
                reason = str(e)
                passed = False
                break

            process.terminate()
            process.join()
            logging.debug(
                f"Done, waiting for values from measurement process...")
            values = conn2.recv()

            if isinstance(values, Exception):
                raise values

            logging.debug(f"Values: {values}")
            time_list.append(values[0])
            energy_list.append(values[1])
            power_list.append(values[2])
            

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

        # self.report_builder.add_case(time_list=time_list,
        #                              energy_list=energy_list,
        #                              power_list=power_list,
        #                              test_name=self.test_id,
        #                              passed=True if exc_type is None else False,
        #                              reason=str(exc_value) if exc_value is not None else "")
