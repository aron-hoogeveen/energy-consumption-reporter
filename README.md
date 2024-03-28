# Scenario Energy Report

**Authors:** Delano Flipse, Rodin Haker, Aron Hoogeveen


## Setup

This project uses Python 3.10.

## Description

This tool offers developers a method to gauge energy and power consumption at a per-function level. By default it leverages the [spec-power-model](https://github.com/green-coding-solutions/spec-power-model) developed by Green Coding Solutions for power measurement, utilizing CPU utilization of the program executing the function under test.

The tool automatically detects the hardware specification of the system it is used on and trains the model to accurately capture the energy consumption patterns. This process utilizes the [TDP list](https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/hardware/cpu\_power.csv}{https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/hardware/cpu\_power.csv) provided by CodeCarbon to retrieve the TDP for the CPU.

The measuring process can be started in two ways, as discussed in [Usage](#Usage). It will then proceed to measure the program from a separate process.

Finally, you can set up the tool to output a JSON file, print the report in the terminal, both, or neither.

## Dependencies

### Windows
As of now, no specific requirements are identified.

### Linux

- [lm-sensors](https://github.com/lm-sensors/lm-sensors) - the command `sensors -j` is used for extracting information about the CPU temperature.

## Installation

### Using Poetry (Recommended)
```console
poetry add energy_consumption_reporter
```

### Using PIP
```console
pip install energy_consumption_reporter
```

### Submodule / Download
Alternatively, you have the option to download this repository or add it as a submodule and integrate it into your own projects. This approach allows you to customize the tool according to your preferences and make any necessary adjustments as needed.

#### Add submodule
```console
git submodule add https://github.com/aron-hoogeveen/energy-consumption-reporter.git <destination-folder>
```

#### Pull submodule
```console
git submodule update --init
```

#### Update submodule
```console
git submodule update --remote --merge
```

## Usage

First you must import the module:

```python
from energy_consumption_reporter.energy_tester import EnergyTester, OutputType
```

There are two main ways to use this project:

1. Implement the decorator to test a function. You can specify the number of iterations as a parameter.

``` python
@EnergyTest.energy_test(2)
def test_func():
    def fib(n):
        if n <= 1:
            return n
        else:
            return fib(n-1) + fib(n-2)

    assert fib(37) == 24157817, "Not equal"
```

2. Utilize a with statement to test a specific code segment once.

``` python
def test_func3():
    with EnergyTest() as test:
        def fib(n):
            if n <= 1:
                return n
            else:
                return fib(n-1) + fib(n-2)

        assert fib(35) == 9227465, "Not equal"
```

You have the flexibility to configure the following custom parameters:
- Model (default = [spec-power-model](https://github.com/green-coding-solutions/spec-power-model) by Green Coding Solutions)
- Report name (default = CPU Energy Test Report)
- Report description (default = empty)
- Option to save a report in JSON format (default = NONE)

These parameters need to be configured before calling the functions. Refer to the [example.py](https://github.com/aron-hoogeveen/energy-consumption-reporter/blob/main/example.py) file for more details and examples.

``` python
EnergyTest().set_model(MyCustomModel)
EnergyTest().set_report_name("Custom Report Name")
EnergyTest().set_report_description("Custom Report Description")
EnergyTest().set_save_report(OutputType.PRINT_JSON)
```

If the option 'set_save_report' is set to True, the tool will generate [a JSON file](https://github.com/aron-hoogeveen/energy-consumption-reporter/blob/main/reporterdashboard/example-reports/report1.json) containing the output data. When set to False it prints the same information to the terminal.

## Pytest plugin

This tool has been integrated into [pytest-energy-reporter](https://github.com/delanoflipse/pytest-energy-reporter), a pytest plugin designed to seamlessly incorporate energy metrics into pytest's reporting capabilities.