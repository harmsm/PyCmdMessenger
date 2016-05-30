__description__ = \
"""
Basic error classes for this module.
"""
__author__ = "Michael J. Harms"
__date__ = "2016-05-30"

class PyCmdMessengerError(Exception):
    """
    Base exception for PyCmdMessenger.
    """
    
    pass

class PCMMangledMessageError(PyCmdMessengerError):
    """
    Error thrown with message is recieved in unreadable form.
    """
    
    pass

class PCMBadSpecError(PyCmdMessengerError):
    """
    Error thrown if user specifies something wrong with system.
    """

    pass
