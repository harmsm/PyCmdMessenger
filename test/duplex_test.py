#!/usr/bin/env python3
import random
import sys
import PyCmdMessenger

__description__ = """
Test ability to send duplex data (e.g. read args while sending them out with
an unterminated command).
"""
__author__ = "Michael J. Harms"
__date__ = "2016-06-04"
__usage__ = "./duplex.py serial_device (like /dev/ttyACM0)"


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    try:
        serial_device = argv[0]
    except IndexError:
        err = "Incorrect arguments. Usage:\n\n{}\n\n".format(__usage__)
        raise IndexError(err)

    a = PyCmdMessenger.ArduinoBoard(serial_device, 115200)
    c = PyCmdMessenger.CmdMessenger(a, [["double_ping", "fff"],
                                        ["double_pong", "fff"]])

    for i in range(10):

        values = [2*(random.random() - 0.5),
                  2*(random.random() - 0.5),
                  2*(random.random() - 0.5)]

        c.send("double_ping", *values)
        received_cmd = c.receive()

        cmd = received_cmd[0]
        received = received_cmd[1]

        success = 1
        for i, r in enumerate(received):
            if abs(r - values[i]) < 0.000001:
                success *= 1
            else:
                success = 0

        if success == 0:
            success = "FAIL"
        else:
            success = "PASS"

        print("{:10s} --> {} --> {} --> {:4}".format(cmd,
                                                     values,
                                                     received,
                                                     success))

if __name__ == "__main__":
    main()
