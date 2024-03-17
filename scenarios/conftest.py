import time
import pytest

# Dictionary to store method execution times
method_times = {}

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    if call.when == 'call':
        method_name = item.name
        if method_name not in method_times:
            method_times[method_name] = []
        # Define the number of repetitions
        repetitions = 3
        for _ in range(repetitions):
            start_time = time.time()
            item.ihook.pytest_pyfunc_call(pyfuncitem=item)
            end_time = time.time()
            method_times[method_name].append(end_time - start_time)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if method_times:
        terminalreporter.write_sep('-', 'Time spent on each test method')
        for method_name, times in method_times.items():
            total_time = sum(times)
            mean_time = total_time / len(times)
            terminalreporter.write_line(f"{method_name}: Mean Time - {mean_time:.2f}s")
