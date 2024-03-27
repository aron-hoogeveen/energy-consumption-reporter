import inspect
import logging
from multiprocessing import Pipe
from multiprocessing.managers import BaseManager

from energy_consumption_reporter.energy_model import EnergyModel
from functools import wraps

from energy_consumption_reporter.measure_process import MeasureProcess
from energy_consumption_reporter.singleton import SingletonMeta
from energy_consumption_reporter.report_builder import ReportBuilder

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class EnergyTester(metaclass=SingletonMeta):

    def __init__(self) -> None:
        self.conn1, self.conn2 = Pipe()
        self.process = None
        self.save_report = False

        BaseManager.register('model', EnergyModel)
        manager = BaseManager()
        manager.start()
        self.model = manager.model()  # type: ignore

        self.report_name = "CPU Energy Test Report"

        self.report_builder = ReportBuilder(
            name=self.report_name,
            model_name="EnergyModel",
        )
        self.report_builder.generate_report()

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop(exc_type, exc_value, traceback)
        if self.save_report:
            self.report_builder.save_report()

    @staticmethod
    def energy_test(times=1):
        def decorate(func):
            @wraps(func)
            def wrapper_func(*args, **kwargs):
                EnergyTester().test(func, times)

            return wrapper_func
        return decorate

    # Set custom model (Default = EnergyModel)
    def set_model(self, model):
        BaseManager.register("model", model)
        manager = BaseManager()
        manager.start()
        self.model = manager.model()  # type: ignore
        self.report_builder.set_model_name(model.__name__)

    # Set whether to save report (Default = False)
    def set_save_report(self, save_report: bool):
        self.save_report = save_report

    # Set custom report name
    def set_report_name(self, name: str):
        self.report_name = name
        self.report_builder.set_name(name)

    # Set custom report description
    def set_report_description(self, description: str):
        self.report_builder.set_description(description)

    def test(self, func, times, func_name=None):
        if func_name is None:
            func_name = func.__qualname__

        energy_list = []
        power_list = []
        time_list = []
        passed = True
        stop = False
        result = None
        error = None
        for i in range(times):
            if stop:
                break

            nth = i + 1
            logging.debug(f"Test {func_name}, Iteration: {nth}")

            process = MeasureProcess(self.conn1, self.model)
            process.start()
            reason = ""

            logging.debug(
                f"Running method {func_name}...")
            try:
                result = func()
                error = None
            except AssertionError as e:
                result = None
                error = e

                reason = str(e)
                passed = False
                stop = True

            process.terminate()
            process.join()

            logging.debug(
                f"Done, waiting for values from measurement process...")
            values = self.conn2.recv()

            if isinstance(values, Exception):
                raise values

            logging.debug(f"Values: {values}")
            time_list.append(values[0])
            energy_list.append(values[1])
            power_list.append(values[2])

        self.report_builder.add_case(time_list=time_list,
                                     energy_list=energy_list,
                                     power_list=power_list,
                                     test_name=func_name,
                                     passed=passed,
                                     reason=reason)

        if self.save_report:
            self.report_builder.save_report()
        return {"time": time_list, "energy": energy_list, "power": power_list, "result": result, "exception": error}

    def start(self):
        self.process = MeasureProcess(self.conn1, self.model)
        self.process.start()

    def stop(self, exc_type, exc_value, traceback):
        if self.process is None:
            return

        self.process.terminate()
        self.process.join()

        stack = inspect.stack()
        stack = stack[1:6]
        func = stack[1].function

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
                                     test_name=func,
                                     passed=True if exc_type is None else False,
                                     reason=str(exc_value) if exc_value is not None else "")
