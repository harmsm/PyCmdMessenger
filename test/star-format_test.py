#!/usr/bin/env python3
__description__ = \
"""
Test the use of the * format. It sends a random list of longs (without a pre-
specified length of the list) and then receives it (again, without a specified
list length). 
"""
__author__ = "Michael J. Harms"
__date__ = "2016-06-08"
__usage__ = "./duplex.py serial_device (like /dev/ttyACM0)"

import random, sys
import PyCmdMessenger

def main(argv=None):
    
    if argv == None:
        argv = sys.argv[1:] 

    try:
        serial_device = argv[0]
    except IndexError:
        err = "Incorrect arguments. Usage:\n\n{}\n\n".format(__usage__)
        raise IndexError(err)

    a = PyCmdMessenger.ArduinoBoard(serial_device,115200)
    c = PyCmdMessenger.CmdMessenger(a,[["multi_ping","i*"],
                                       ["multi_pong","i*"]])

    
    for i in range(10):
       
        num_args = random.choice(range(1,10)) 
        sent_values = [random.choice(range(10)) for j in range(num_args)]
        c.send("multi_ping",len(sent_values),*sent_values)

        received_cmd = c.receive()

        cmd = received_cmd[0]
        received = received_cmd[1]

        success = 1
        for i, r in enumerate(received):
            if sent_values[i] == r:
                success *= 1
            else:
                success = 0

        if success == 0:
            success = "FAIL"
        else:
            success = "PASS"

        print("{:10s} --> {} --> {} --> {:4}".format(cmd,
                                                     sent_values,
                                                     received,
                                                     success))

if __name__ == "__main__":
    main()
