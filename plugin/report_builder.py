import datetime
import json
import re
import subprocess
import psutil


class ReportBuilder:
    def __init__(self, name: str, description=""):
        self.name = name
        self.description = description
        self.time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.version = 0
        self.report = {"results": {}}

    def generate_report(self):
        self.version += 1

        self.report["results"].update({"name": self.name})
        self.report["results"].update({"description": self.description})
        self.report["results"].update({"version": self.version})
        self.report["results"].update({"software_version": "v0.1BETA"})
        # TODO: get the commit hash from the git repo
        self.report["results"].update({"commit": ""})
        self.report["results"].update({"date": self.time})
        self.report["results"].update({"model": "XGBRegressor"})

        sensor_data = json.loads(subprocess.check_output(
            ["sensors", "-j"]).decode("utf-8"))
        temp = sensor_data.get(
            "k10temp-pci-00c3").get("Tctl").get("temp1_input")

        cpuinfo = subprocess.check_output('lscpu', encoding='UTF-8')
        match = re.search(r'Model name:\s*(.*)', cpuinfo)

        pc_name = subprocess.check_output(
            'hostname', encoding='UTF-8').removesuffix("\n")

        hardware = {
            "PC_name": pc_name,
            "CPU_name": str(match.group(1) if match else "Unknown CPU"),
            "CPU_temp": temp if temp else -1,
            "CPU_freq": psutil.cpu_freq().max,
        }

        self.report["results"].update({"hardware": hardware})

        self.report["results"].update({"cases": []})

    def add_case(self, time_list, energy_list, power_list, test_name, passed, reason):
        energy_list = [
            int(item*10000) / 10000 for item in energy_list]

        power_list = [
            int(item*10000) / 10000 for item in power_list]

        case = {
            "name": test_name,
            "result": "pass" if passed else "fail",
            "reason": reason,
            "N": len(time_list),
            "execution_time": time_list,
            "energy": energy_list,
            "power": power_list,
        }

        self.report["results"]["cases"].append(case)

    def save_report(self, file_path=None):
        if file_path is None:
            file_path = "EnergyReport-" + self.time + ".json"
        with open(file_path, 'w') as file:
            file.write(json.dumps(self.report, indent=4))

    def print_report(self):
        print(json.dumps(self.report, indent=4))
