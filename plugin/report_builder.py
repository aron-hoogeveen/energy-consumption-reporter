import json
import re
import subprocess
import time


class ReportBuilder:
    def __init__(self, cpu_info: dict, total_time: float, energy: float, power: float, name: str, description=""):
        self.cpu_info = cpu_info
        self.total_time = total_time
        self.energy = energy
        self.power = power
        self.name = name
        self.description = description
        self.version = 0
        self.report = {"results": {}}

    def generate_report(self):
        self.version += 1

        self.report["results"].update({"name": self.name})
        self.report["results"].update({"description": self.description})
        self.report["results"].update({"version": str(self.version)})
        self.report["results"].update({"software_version": "v0.1BETA"})
        # TODO: get the commit hash from the git repo
        self.report["results"].update({"commit": ""})
        self.report["results"].update(
            {"date": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())})
        self.report["results"].update({"model": "XGBRegressor"})

        # run sensors -j to get the temperature of the CPU
        sensor_data = json.loads(subprocess.check_output(
            ["sensors", "-j"]).decode("utf-8"))
        temp = sensor_data.get(
            "k10temp-pci-00c3").get("Tctl").get("temp1_input")

        cpuinfo = subprocess.check_output('lscpu', encoding='UTF-8')
        match = re.search(r'Model name:\s*(.*)', cpuinfo)

        if not match:
            match = None

        pc_name = subprocess.check_output(
            'hostname', encoding='UTF-8').removesuffix("\n")

        hardware = {
            "PC_name": pc_name,
            "CPU_name": str(match.group(1) if match else "Unknown CPU"),
            "CPU_temp": str(temp),
            "CPU_freq": str(self.cpu_info["cpu-freq"]),
        }

        self.report["results"].update({"hardware": hardware})

        cases = [
            {
                "name": "test1",  # TODO add the name of the test
                "result": "pass",  # TODO add the result of the test
                "reason": "reason",  # TODO add the reason for the result
                "N": "1",  # TODO add the number of tests
                # TODO add the execution time of all test rounds
                "execution_time": str(self.total_time),
                # TODO add the energy consumption of all test rounds
                "energy": "{:.4f}".format(self.energy),
                # TODO add the power consumption of all test rounds
                "power": "{:.4f}".format(self.power),
            }
        ]

        self.report["results"].update({"cases": cases})

    def save_report(self, file_path):
        with open(file_path, 'w') as file:
            file.write(json.dumps(self.report, indent=4))

    def print_report(self):
        print(json.dumps(self.report, indent=4))
