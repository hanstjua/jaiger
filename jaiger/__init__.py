import multiprocessing
try:
    multiprocessing.set_start_method('spawn')
except RuntimeError:
    pass

from .main import Jaiger