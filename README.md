# Scenario Energy Report

**Authors:** Delano Flipse, Rodin Haker, Aron Hoogeveen


## Setup

This project uses Python 3.10.

## Description

<!-- TODO add project description -->

## Usage

There are two main ways to use this project:

1. Use the decorator to test a function. You can provide the amount of times it has to run as a parameter.

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

2. Use a with statement to test a particular piece of code once

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

You can set up the following custom parameters:
- model
- report name
- report description
- whether to save a report (in JSON format)

``` python
EnergyTest().set_model(EnergyModel)
EnergyTest().set_report_name("Custom Report Name")
EnergyTest().set_report_description("Custom Report Description")
EnergyTest().set_save_report(True)
```