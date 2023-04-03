"""
pyOpenBeken
~~~~~~~
An easier way to manage your OpenBeken devices.
"""


__version__ = "0.0.1"
__author__ = "Gonzalo Garcia"


from .core import pyopenbeken
from .boardmanager import BoardManager
from .utils import ThreadManager,networkScan