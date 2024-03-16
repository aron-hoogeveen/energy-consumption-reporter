import logging
from energy_test import EnergyTest

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

    assert fib(35) == 9227465, "Not equal"


@EnergyTest.energy_test(2)
def test_func2():
    def fib(n):
        if n <= 1:
            return n
        else:
            return fib(n-1) + fib(n-2)

    assert fib(35) == 92274652, "Not equal"


if __name__ == '__main__':
    test_func()
    test_func2()
