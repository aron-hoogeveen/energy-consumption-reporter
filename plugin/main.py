import logging
from energy_test import EnergyTest
from energy_model import EnergyModel

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


@EnergyTest.energy_test(2)
def test_func():
    def fib(n):
        if n <= 1:
            return n
        else:
            return fib(n-1) + fib(n-2)

    assert fib(37) == 24157817, "Not equal"


@EnergyTest.energy_test(2)
def test_func2():
    def fib(n):
        if n <= 1:
            return n
        else:
            return fib(n-1) + fib(n-2)

    assert fib(35) == 92274652, "Not equal"


def test_func3():
    with EnergyTest() as test:
        def fib(n):
            if n <= 1:
                return n
            else:
                return fib(n-1) + fib(n-2)

        assert fib(35) == 9227465, "Not equal"


if __name__ == '__main__':
    # EnergyTest().set_model(EnergyModel)
    EnergyTest().set_report_name("Custom Report Name")
    EnergyTest().set_report_description("Custom Report Description")
    EnergyTest().set_save_report(True)

    test_func()
    test_func2()
    test_func3()
