from threading import Lock

import psutil


class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances = {}

    _lock: Lock = Lock()

    def __init__(self, name, bases, mmbs):
        if psutil.WINDOWS:
            return
        super(SingletonMeta, self).__init__(name, bases, mmbs)
        self._instances[self] = super(SingletonMeta, self).__call__()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]
