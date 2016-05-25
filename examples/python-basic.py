# ------------------------------------------------------------------------------
# Python program using the library to interface with the arduino sketch above.
# ------------------------------------------------------------------------------

import PyCmdMessenger
import time

# Initialize instance of class with appropriate device.  command_names must 
# match names and order from arduino file.
c = PyCmdMessenger.PyCmdMessenger("/dev/ttyACM0",
                                  command_names=("who_are_you",
                                                 "sum_two_ints",
                                                 "result",
                                                 "error"))

# Give time for the device to connect
time.sleep(2)

# Send and receive
c.send("who_are_you")
msg = c.receive()

# should give [TIME_IN_S,"result","Bob"]
print(msg)

# Send with multiple parameters
c.send("sum_two_ints",4,1)
msg = c.receive()

# should give [TIME_IN_S,"result",4,1,5]
print(msg)
