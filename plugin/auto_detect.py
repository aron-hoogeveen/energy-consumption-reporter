import os
import subprocess
import re
import logging
import math
import pandas as pd


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

        match = re.search(r'Model name:\s*(.*)', cpuinfo)
        if match:
            if 'Intel' in match.group(1):
                data['cpu-make'] = 'intel'  # type: ignore
            elif 'AMD' in match.group(1):
                data['cpu-make'] = 'amd'  # type: ignore
            logger.info('Found Make: %s', data['cpu-make'])

            cpu = match.group(1)
            tdp_list = pd.read_csv(
                os.getcwd() + '/plugin/data/cpu_power.csv', sep=',')

            logger.info(cpu)
            tdp = tdp_list[tdp_list.apply(
                lambda row: row['Name'] in cpu, axis=1)]
            tdp = tdp[tdp['Name'].apply(len) == tdp['Name'].apply(len).max()]
            logger.info('Found TDP: %s', tdp)
            if not tdp.empty:
                data['tdp'] = tdp['TDP'].values[0]  # type: ignore
                logger.info('Found TDP: %s', data['tdp'])
            else:
                logger.info('Could not find TDP. Using default 100')
                data['tdp'] = 100  # type: ignore

        match = re.search(r'Architecture:\s*(\w+)', cpuinfo)
        if match:
            data['architecture'] = match.group(1)  # type: ignore
            logger.info('Found Architecture: %s', data['architecture'])
            spec_data = pd.read_csv(
                os.getcwd() + '/plugin/data/spec_data_cleaned.csv', sep=',')
            if data['architecture'] not in spec_data['Architecture'].unique():
                if data['cpu-make'] == 'intel':
                    logger.info(
                        'Architecture not in training data. Using default xeon.')
                    data['architecture'] = 'xeon'  # type: ignore
                elif data['cpu-make'] == 'amd':
                    logger.info(
                        'Architecture not in training data. Using default epyc-gen3.')
                    data['architecture'] = 'epyc-gen3'  # type: ignore
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
