# custom_reporter.py

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
        method_times[method_name].append(call.stop - call.start)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if method_times:
        terminalreporter.write_sep('-', 'Time spent on each test method')
        for method_name, times in method_times.items():
            total_time = sum(times)
            avg_time = total_time / len(times)
            terminalreporter.write_line(f"{method_name}: Total Time - {total_time:.2f}s, Average Time - {avg_time:.2f}s")
