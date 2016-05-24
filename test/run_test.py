#!/usr/bin/env python3
__description__ = \
"""
run_tests.py

Run a series of test send/recieve commands to an attached arduino.  This assumes
that the arduino sketch in this directory has been compiled and loaded onto the 
arduino.  Note the CmdMessenger.* files are taken from that project:
https://github.com/thijse/Arduino-CmdMessenger 
"""
__author__ = "Michael J. Harms"
__date__ = "2016-05-23"
__usage__ = "./run_tests.py DEVICE (where DEVICE is like /dev/ttyACM0)"

import sys
import PyCmdMessenger

def main(argv=None):
    """
    Parse command line and run tests.
    """

    if argv == None:
        argv = sys.argv[1:]

    try:
        serial_device = argv[0]
    except IndexError:
        err = "Incorrect arguments. Usage: \n\n{}\n\n".format(__usage__)
        raise IndexError(err)

    # Initialize instance of class.
    c = PyCmdMessenger.PyCmdMessenger(serial_device)

    #--------------------------------------------------------------------------

    print("Testing simple send/recieve... ",end="")
    
    # Send and recieve
    c.send("who_are_you")
    msg = c.recieve()

    if msg[1] == "my_name_is" and msg[2] == "Bob":
        print("PASS")
    else:
        print("FAIL -> output is: {}".format(msg))

    #--------------------------------------------------------------------------

    print("Testing multiread... ",endl="")

    for i in range(10):
        c.send("who_are_you")

    time.sleep(1)

    msgs = c.recieve_all()
    results = [] 
    for i in range(len(msgs)):
        results.append(msgs[i][1] == "my_name_is" and msgs[i][2] == "Bob")

    if sum(results) == 10:
        print("PASS")
    else:
        print("FAIL")
        
    #--------------------------------------------------------------------------

    print("Testing listener...",endl="")
    c.listen(0.1)
    for i in range(10):
        c.send("who_are_you")

    time.sleep(2)

    msgs = c.recieve_from_listener()
    results = []
    for i in range(len(msgs)):
        results.append(msgs[i][1] == "my_name_is" and msgs[i][2] == "Bob")

    c.stop_listening()

    if sum(results) == 10:
        print("PASS")
    else:
        print("FAIL")

    #--------------------------------------------------------------------------

    print("Testing listener and threading...",endl="")
    c.listen(0.5)
    for i in range(5):
        c.send("who_are_you")

    c.send("bad_command")

    for i in range(5):
        c.send("who_are_you")

    time.sleep(7)

    msgs = c.recieve_from_listener()

    try:
        results = []
        for i in range(5):
            results.append(msgs[i][1] == "my_name_is" and msgs[i][2] == "Bob")
        
        results.append(msgs[5][1] == "error"
                       and msgs[i][2] == "Command without callback.")

        for i in range(6,11):
            results.append(msgs[i][1] == "my_name_is" and msgs[i][2] == "Bob")
    except:
        results = []

    if sum(results) == 11:
        print("PASS")
    else:
        print("FAIL")

        
if __name__ == "__main__":
    main()    

