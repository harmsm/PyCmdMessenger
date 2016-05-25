
# ------------------------------------------------------------------------------
# Python program using the library to interface with the arduino sketch above,
# demonstrating the use of the listener.
# ------------------------------------------------------------------------------

import time
import PyCmdMessenger

c = PyCmdMessenger.PyCmdMessenger("/dev/ttyACM0",
                                  command_names=("who_are_you",
                                                 "sum_two_ints",
                                                 "result",
                                                 "error"))

time.sleep(2)

# start listening
c.listen()

# stop listening
for i in range(10):
    c.send("who_are_you")

# Do other stuff.  The listener is capturing the output from the arduino on its
# own thread right now.
time.sleep(5)

# Now grab the messages it received in the background.  This should be a list of
# messages with timestamps.
messages = c.receive_from_listener()
for m in messages:
    print(m)

c.stop_listening()
