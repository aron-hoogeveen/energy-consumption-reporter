import os
import subprocess
import re
import logging
import math
import platform
from typing import Optional

import pandas as pd
import psutil


class CPUInfo:
    def __init__(self, chips: Optional[int] = None, cores: Optional[int] = None, threads: Optional[int] = None, freq: Optional[int] = None, tdp: Optional[int] = None, mem: Optional[int] = None, make: Optional[str] = None, architecture: Optional[str] = None):
        self.chips = chips
        self.cores = cores
        self.threads = threads
        self.freq = freq  # in Mhz
        self.tdp = tdp  # in W
        self.mem = mem  # in GB
        self.make = make
        self.architecture = architecture

    def __dict__(self):
        return {
            'chips': self.chips,
            'cores': self.cores,
            'threads': self.threads,
            'freq': self.freq,
            'tdp': self.tdp,
            'mem': self.mem,
            'make': self.make,
            'architecture': self.architecture
        }


def get_cpu_info_linux(logger):
    data = CPUInfo()

    try:
        cpuinfo = subprocess.check_output('lscpu', encoding='UTF-8')
        match = re.search(r'On-line CPU\(s\) list:\s*(0-)?(\d+)', cpuinfo)
        if match:
            data.threads = int(match.group(2))+1
            logger.info('Found Threads: %d', data.threads)
        else:
            logger.info('Could not find Threads. Using default None')

        match = re.search(r'Socket\(s\):\s*(\d+)', cpuinfo)
        if match:
            data.chips = int(match.group(1))
            logger.info(
                'Found Sockets: %d (will take precedence if not 0)', data.chips)
        else:
            logger.info('Could not find Chips/Sockets via lscpu')

        if data.chips:
            match = re.search(r'Core\(s\) per socket:\s*(\d+)', cpuinfo)
            if match:
                cores_per_socket = int(match.group(1))
                data.cores = cores_per_socket * data.chips
                logger.info('Found cores: %d ', data.cores)
            else:
                logger.info('Could not find Cores. Using default None')

        data.freq = int(psutil.cpu_freq().max)
        logger.info('Found Frequency: %s', data.freq)

        match = re.search(r'Model name:\s*(.*)', cpuinfo)
        if match:
            if 'Intel' in match.group(1):
                data.make = 'intel'
            elif 'AMD' in match.group(1):
                data.make = 'amd'
            logger.info('Found Make: %s', data.make)

            cpu = match.group(1)
            tdp_list = pd.read_csv(
                os.getcwd() + '/plugin/data/cpu_power.csv', sep=',')

            tdp = tdp_list[tdp_list.apply(
                lambda row: row['Name'] in cpu, axis=1)]
            tdp = tdp[tdp['Name'].apply(len) == tdp['Name'].apply(len).max()]
            logger.info('Found TDP: %s', tdp)
            if not tdp.empty:
                data.tdp = tdp['TDP'].values[0]
                logger.info('Found TDP: %s', data.tdp)
            else:
                logger.info('Could not find TDP. Using default 100')
                data.tdp = 100

        match = re.search(r'Architecture:\s*(\w+)', cpuinfo)
        if match:
            data.architecture = match.group(1)
            logger.info('Found Architecture: %s', data.architecture)
            spec_data = pd.read_csv(
                os.getcwd() + '/plugin/data/spec_data_cleaned.csv', sep=',')
            if data.architecture not in spec_data['Architecture'].unique():
                if data.make == 'intel':
                    logger.info(
                        'Architecture not in training data. Using default xeon.')
                    data.architecture = 'xeon'
                elif data.make == 'amd':
                    logger.info(
                        'Architecture not in training data. Using default epyc-gen3.')
                    data.architecture = 'epyc-gen3'

    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info('Could not check for CPU info.')

    try:
        meminfo = subprocess.check_output(
            ['cat', '/proc/meminfo'], encoding='UTF-8', stderr=subprocess.DEVNULL)
        match = re.search(r'MemTotal:\s*(\d+) kB', meminfo)
        if match:
            data.mem = math.ceil(int(match.group(1)) / 1024 / 1024)
            logger.info('Found Memory: %d GB', data.mem)
        else:
            logger.info('Could not find Memory. Using default None')
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info(
            '/proc/meminfo not accesible on system. Could not check for Memory info. Defaulting to None.')

    return data


def get_cpu_make():
    processor_name = platform.processor().lower()
    if 'intel' in processor_name:
        return 'intel'
    elif 'amd' in processor_name:
        return 'amd'
    else:
        return 'unknown'


def get_cpu_info(logger: logging.Logger):
    if platform.system() == 'Linux':
        return get_cpu_info_linux(logger)
    else:
        import psutil

        # fetch CPU info using cpuinfo package
        logger.info('Gathering CPU info')

        chips = 1  # TODO: find a way to get this info
        freq = int(psutil.cpu_freq().max)
        threads = psutil.cpu_count(logical=True)
        cores = psutil.cpu_count(logical=False)
        tdp = 0  # TODO: find a way to get this info
        mem = math.ceil(psutil.virtual_memory().total / 1024 / 1024 / 1024)
        make = get_cpu_make()
        architecture = None  # TODO: find a way to get this info

        # write summary to logger
        logger.info('CPU info for: %s', platform.processor())
        logger.info('Found # of chips: %d', chips)
        logger.info('Found # of cores: %d', cores)
        logger.info('Found # of threads: %d', threads)
        logger.info('Found frequency: %d Mhz', freq)
        logger.info('Found TDP: %d W', tdp)
        logger.info('Found memory: %d GB', mem)
        logger.info('Found make: %s', make)
        logger.info('Found architecture: %s', architecture)

        # return CPU info
        return CPUInfo(
            chips=chips,
            freq=freq,
            threads=threads,
            cores=cores,
            make=make,
            tdp=tdp,
            mem=mem,
            architecture=architecture
        )


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
