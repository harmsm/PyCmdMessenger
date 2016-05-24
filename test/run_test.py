#!/usr/bin/env python3
__description__ = \
"""
run_tests.py

Run a series of test send/receive commands to an attached arduino.  This assumes
that the arduino sketch in this directory has been compiled and loaded onto the 
arduino.  Note the CmdMessenger.* files are taken from that project:
https://github.com/thijse/Arduino-CmdMessenger 
"""
__author__ = "Michael J. Harms"
__date__ = "2016-05-23"
__usage__ = "./run_tests.py DEVICE (where DEVICE is like /dev/ttyACM0)"

import sys, time
import PyCmdMessenger

def check_connection(c,cmd,max_num_attempts=50,delay=0.1):
    """
    Make sure the connection is made before doing tests.
    """

    has_connected = False 
    num_attempts = 0
    while not has_connected and num_attempts < max_num_attempts:

        c.send(cmd)
        
        try:
            msg = c.receive()
        except ValueError:
            msg = True

        if msg != None:
            return num_attempts * delay
        else:
            num_attempts += 1
            time.sleep(delay)  

    return -1

def try_cmd(c,cmd,expected_result):
    """
    Try a given command, comparing the output to th expected_result
    """

    # Make the command into a list
    if type(cmd) != list and type(cmd) != tuple:
        cmd = [cmd]

    # print the command
    print("{:20} ".format(cmd[0]),end="")

    # Turn the expected_results into a tuple
    if type(expected_result) != tuple:
        if type(expected_result) == list:
            expected_result = tuple(expected_result)
        else:
            expected_result = tuple([expected_result])

    # send the command and receive its output
    c.send(*cmd)
    msg = c.receive()

    # make sure results match expectation
    if expected_result != None and msg == None:
        print("... FAIL.  None returned.  Expected: {}".format(expected_result))
        return
 
    if msg[1] != "result":
        print("... FAIL.  Command {} returned.  Expected {}".format(msg[1],msg[0]))
 
    result = tuple(msg[2])
 
    if result == expected_result:
        print("... PASS")
    else:
        print("... FAIL.  Recieved {}. Expected {}".format(result,expected_result))

def try_cmd_multi(c,cmd,expected_result,num_reps=10,use_listener=False):
    """
    Try the command num_reps times in a row, making sure that each has the
    expected_output. 
    """

    # Make the command into a list
    if type(cmd) != list and type(cmd) != tuple:
        cmd = [cmd]

    # print the command
    print("{:20} ".format(cmd[0]),end="")

    # Turn the expected_results into a tuple
    if type(expected_result) != tuple:
        if type(expected_result) == list:
            expected_result = tuple(expected_result)
        else:
            expected_result = tuple([expected_result])

    # listen, if requested
    if use_listener:
        c.listen(0.1)

    # send the same command num_reps times in a row
    for i in range(num_reps):
        c.send(*cmd)
  
    # get the messages 
    if use_listener:
        time.sleep(3)
        msgs = c.receive_from_listener()
        c.stop_listening()
    else:
        msgs = c.receive_all()

    # make sure that the output messages have the same length
    if len(msgs) != num_reps:
        print("... FAIL. Only {} of {} messages recieved.".format(len(msgs),num_reps))
        return

    # Parse the results, making sure we see what is expected
    results = [] 
    for i in range(len(msgs)):

        r1 = msgs[i][1]
        r2 = tuple(msgs[i][2])
        
        if r1 != "result":
            print("... FAIL. Command {} returned. Expected {}".format(r1,"result"))
            return

        if r2 != expected_result:
            print("... FAIL. Recieved {}. Expected {}.".format(r2,expected_result))
            return

    print("... PASS")


def try_cmd_multithread(c,cmd1,cmd2,expected_result1,expected_result2,num_reps=10):
    """
    Try cmd1 and cmd2 with multithreading.  Execute cmd1 with a listner, then
    cmd2 and then cmd1.  Make sure the listner gets the coorect output values.
    """

    # turn commands into lists
    if type(cmd1) != list and type(cmd1) != tuple:
        cmd1 = [cmd1]

    if type(cmd2) != list and type(cmd2) != tuple:
        cmd2 = [cmd2]

    # print the command
    print("{:20} ".format("multithread"),end="")

    # turn expected_results into tuples
    if type(expected_result1) != tuple:
        if type(expected_result1) == list:
            expected_result1 = tuple(expected_result1)
        else:
            expected_result1 = tuple([expected_result1])

    if type(expected_result2) != tuple:
        if type(expected_result2) == list:
            expected_result2 = tuple(expected_result2)
        else:
            expected_result2 = tuple([expected_result2])

    # flip on listener
    c.listen(0.1)

    # Run the command, collecting expected results for command 1...
    expected_results = []
    for i in range(int(num_reps/2)):
        c.send(*cmd1)
        expected_results.append(expected_result1)

    # ... command 2 ...
    c.send(*cmd2)
    expected_results.append(expected_result2)

    # ... and then command 1.
    for i in range(int(num_reps/2)):
        c.send(*cmd1)
        expected_results.append(expected_result1)
   
    time.sleep(num_reps*2*0.1)

    # Receive the messages
    msgs = c.receive_from_listener()
    c.stop_listening()

    # make sure there are enought messages 
    N = int(num_reps/2)*2 + 1
    if len(msgs) != N:
        print("... FAIL. Only {} of {} messages recieved.".format(len(msgs),N))
        return

    # see if the results match
    results = [] 
    for i in range(N):

        r1 = msgs[i][1]
        r2 = tuple(msgs[i][2])
        
        if r1 != "result":
            print("... FAIL. Command {} returned. Expected {}".format(r1,"result"))
            return 

        if r2 != expected_results[i]:
            print("... FAIL. Recieved {}. Expected {}".format(r2,expected_results[i]))
            return

    print("... PASS")



def main(argv=None):
    """
    Parse command line and run tests.
    """

    # Parse command line
    if argv == None:
        argv = sys.argv[1:]

    try:
        serial_device = argv[0]
    except IndexError:
        err = "Incorrect arguments. Usage: \n\n{}\n\n".format(__usage__)
        raise IndexError(err)



    # Run a wide variety of tests
    print("CONNECTING")
    print("------------------------------------------------------------------")

    # Initialize instance of class.
    c = PyCmdMessenger.PyCmdMessenger(serial_device,
                                      command_names=["send_string",
                                                     "send_float",
                                                     "send_int",
                                                     "send_two_int",
                                                     "receive_string",
                                                     "receive_float",
                                                     "receive_int",
                                                     "receive_two_int",
                                                     "result",
                                                     "error"])
    connect_time = check_connection(c,"send_string")
    if connect_time < 0:
        print("FAIL.  Could not connect.")
        err = "connection could not be made"
        raise SystemError(err)

    else:
        print("PASS.  Connection made in ~{} s".format(connect_time))


    print()
    print("SEND/RECIEVE")
    print("------------------------------------------------------------------")
    
    # Send and receive
    try_cmd(c,"send_string","A string with /, and /; escape")
    try_cmd(c,"send_float",99.9)
    try_cmd(c,"send_int",-10)
    try_cmd(c,"send_two_int",[-10,10])
    try_cmd(c,["receive_string","string"],"got it!")
    try_cmd(c,["receive_float",99.9],999.0)
    try_cmd(c,["receive_int",-10],-100)
    try_cmd(c,["receive_two_int",-10,10],[-100,100])
    
    #--------------------------------------------------------------------------

    print()
    print("RECEIVE ALL")
    print("------------------------------------------------------------------")
    try_cmd_multi(c,"send_string","A string with /, and /; escape")
    try_cmd_multi(c,"send_float",99.9)
    try_cmd_multi(c,"send_int",-10)
    try_cmd_multi(c,"send_two_int",[-10,10])
    try_cmd_multi(c,["receive_string","string"],"got it!")
    try_cmd_multi(c,["receive_float",99.9],999.0)
    try_cmd_multi(c,["receive_int",-10],-100)
    try_cmd_multi(c,["receive_two_int",-10,10],[-100,100])
 
    #--------------------------------------------------------------------------

    print()
    print("USE LISTENER")
    print("------------------------------------------------------------------")
    try_cmd_multi(c,"send_string","A string with /, and /; escape",use_listener=True)
    try_cmd_multi(c,"send_float",99.9,use_listener=True)
    try_cmd_multi(c,"send_int",-10,use_listener=True)
    try_cmd_multi(c,"send_two_int",[-10,10],use_listener=True)
    try_cmd_multi(c,["receive_string","string"],"got it!",use_listener=True)
    try_cmd_multi(c,["receive_float",99.9],999.0,use_listener=True)
    try_cmd_multi(c,["receive_int",-10],-100,use_listener=True)
    try_cmd_multi(c,["receive_two_int",-10,10],[-100,100],use_listener=True)
        
    #--------------------------------------------------------------------------

    print()
    print("USE LISTENER WITH WRITE IN MIDDLE")
    print("------------------------------------------------------------------")
    try_cmd_multithread(c,"send_string",["receive_float",99.9],"A string with /, and /; escape",999.0)
    try_cmd_multithread(c,["receive_string","string"],"send_two_int","got it!",[-10,10])

# If run from the command line...        
if __name__ == "__main__":
    main()    

