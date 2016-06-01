__description__ = \
"""
Python class for interfacing with CmdMessenger arduino serial communications
library.
"""
__author__ = "Michael J. Harms"
__date__ = "2016-05-23"
__all__ = ["PyCmdMessenger","arduino"]

from .PyCmdMessenger import CmdMessenger as CmdMessenger
from .arduino import ArduinoBoard as ArduinoBoard
