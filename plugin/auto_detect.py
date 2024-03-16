import subprocess
import re
import logging
import math


def get_cpu_info(logger: logging.Logger, verbose: bool = False):
    if not verbose:
        logger.disabled = True

    data = {
        'cpu-freq': None,
        'cpu-threads': None,
        'cpu-cores': None,
        'tdp': None,
        'ram': None,
        'cpu-make': None,
        'cpu-chips': None,
        'architecture': None
    }

    try:
        file_path = '/sys/class/powercap/intel-rapl/intel-rapl:0/name'
        with open(file_path, 'r', encoding='UTF-8') as file:
            domain_name = file.read().strip()
            if domain_name != 'package-0':
                raise RuntimeError(
                    f"Domain /sys/class/powercap/intel-rapl/intel-rapl:0/name was not package-0, but {domain_name}")

        file_path = '/sys/class/powercap/intel-rapl/intel-rapl:0/constraint_0_name'
        with open(file_path, 'r', encoding='UTF-8') as file:
            constraint_name = file.read().strip()
            if constraint_name != 'long_term':
                raise RuntimeError(
                    f"Constraint /sys/class/powercap/intel-rapl/intel-rapl:0/constraint_0_name was not long_term, but {constraint_name}")

        file_path = '/sys/class/powercap/intel-rapl/intel-rapl:0/constraint_0_max_power_uw'
        with open(file_path, 'r', encoding='UTF-8') as file:
            tdp = file.read()
            data['tdp'] = int(tdp) / 1_000_000  # type: ignore

        logger.info('Found TDP: %d W', data['tdp'])
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info(
            'Could not read RAPL powercapping info from /sys/class/powercap/intel-rapl')

    try:
        cpuinfo = subprocess.check_output('lscpu', encoding='UTF-8')

        match = re.search(r'On-line CPU\(s\) list:\s*(0-)?(\d+)', cpuinfo)
        if match:
            data['cpu-threads'] = int(match.group(2))+1  # type: ignore
            logger.info('Found Threads: %d', data['cpu-threads'])
        else:
            logger.info('Could not find Threads. Using default None')

        match = re.search(r'Socket\(s\):\s*(\d+)', cpuinfo)
        if match:
            data['cpu-chips'] = int(match.group(1))  # type: ignore
            logger.info(
                'Found Sockets: %d (will take precedence if not 0)', data['cpu-chips'])
        else:
            logger.info('Could not find Chips/Sockets via lscpu')

        if data['cpu-chips']:
            match = re.search(r'Core\(s\) per socket:\s*(\d+)', cpuinfo)
            if match:
                cores_per_socket = int(match.group(1))
                cores = cores_per_socket * data['cpu-chips']
                data['cpu-cores'] = cores  # type: ignore
                logger.info('Found cores: %d ', data['cpu-cores'])
            else:
                logger.info('Could not find Cores. Using default None')

        match = re.search(r'Model name:.*@\s*([\d.]+)\s*GHz', cpuinfo)
        if match:
            data['cpu-freq'] = int(float(match.group(1))*1000)  # type: ignore
            logger.info('Found Frequency: %s', data['cpu-freq'])
        else:
            logger.info('Could not find Frequency. Using default None')

        match = re.search(r'Model name:.*Intel\(R\)', cpuinfo)
        if match:
            data['cpu-make'] = 'intel'  # type: ignore
            logger.info('Found Make: %s', data['make'])

        match = re.search(r'Model name:.*AMD ', cpuinfo)
        if match:
            data['cpu-make'] = 'amd'  # type: ignore
            logger.info('Found Make: %s', data['cpu-make'])

        match = re.search(r'Architecture:\s*(\w+)', cpuinfo)
        if match:
            data['architecture'] = match.group(1)  # type: ignore
            logger.info('Found Architecture: %s', data['architecture'])
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info('Could not check for CPU info.')

    try:
        cpuinfo_proc = subprocess.check_output(
            ['cat', '/proc/cpuinfo'], encoding='UTF-8', stderr=subprocess.DEVNULL)
        match = re.findall(r'cpu MHz\s*:\s*([\d.]+)', cpuinfo_proc)
        if match:
            data['cpu-freq'] = round(max(map(float, match)))  # type: ignore
            logger.info('Found assumend Frequency: %d', data['cpu-freq'])
        else:
            logger.info('Could not find Frequency. Using default None')
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info(
            '/proc/cpuinfo not accesible on system. Could not check for Base Frequency info. Setting value to None.')

    try:
        meminfo = subprocess.check_output(
            ['cat', '/proc/meminfo'], encoding='UTF-8', stderr=subprocess.DEVNULL)
        match = re.search(r'MemTotal:\s*(\d+) kB', meminfo)
        if match:
            data['ram'] = math.ceil(  # type: ignore
                int(match.group(1)) / 1024 / 1024)
            logger.info('Found Memory: %d GB', data['ram'])
        else:
            logger.info('Could not find Memory. Using default None')
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info(
            '/proc/meminfo not accesible on system. Could not check for Memory info. Defaulting to None.')

    logger.disabled = False

    return data
