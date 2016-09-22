#!/usr/bin/env python3
import random
import sys
import PyCmdMessenger

__description__ = """
Test that sends 10000 floats as fast as possible back and forth to the arduino.
It uses random number floats, so this should cover a wide variety of possible
characters in the binary strings that could (possibly) be mangled.

Works with arduino sketch in rapid-float directory.
"""
__author__ = "Michael J. Harms"
__date__ = "2016-06-04"
__usage__ = "./rapid-float.py serial_device (like /dev/ttyACM0)"


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    try:
        serial_device = argv[0]
    except IndexError:
        err = "Incorrect arguments. Usage:\n\n{}\n\n".format(__usage__)
        raise IndexError(err)

    a = PyCmdMessenger.ArduinoBoard(serial_device, 115200)
    c = PyCmdMessenger.CmdMessenger(a, [["double_ping", "d"],
                                        ["double_pong", "d"]])

    for i in range(10000):

        value = 2*(random.random() - 0.5)
        c.send("double_ping", value)
        received_cmd = c.receive()

        cmd = received_cmd[0]
        received = received_cmd[1][0]
        if abs(received - value) < 0.000001:
            success = "PASS"
        else:
            success = "FAIL"

        print("{:10s} --> {:10.6f} --> {:10.6f} --> {:4}".format(cmd,
                                                                 value,
                                                                 received,
                                                                 success))

if __name__ == "__main__":
    main()
