#!/usr/bin/env python3
__description__ = \
"""
Run full test suite on PyCmdMessenger/arduino interface.
"""
__description__ = "Michael J. Harms"
__date__ = "2016-05-30"
__usage__ = "run_test.py serial_device"

import PyCmdMessenger
import time, string, sys, struct, random

BAUD_RATE = 115200

COMMAND_NAMES = ["kCommError",
                 "kComment",
                 "kAcknowledge",
                 "kAreYouReady",
                 "kError",
                 "kAskUsIfReady",
                 "kYouAreReady",
                 "kValuePing",
                 "kValuePong",
                 "kMultiValuePing",
                 "kMultiValuePong",
                 "kRequestReset",
                 "kRequestResetAcknowledge",
                 "kRequestSeries",
                 "kReceiveSeries",
                 "kDoneReceiveSeries",
                 "kPrepareSendSeries",
                 "kSendSeries",
                 "kAckSendSeries"]

TYPE_LIST = ["kBool",
             "kInt16",
             "kInt32",
             "kFloat",
             "kFloatSci",
             "kDouble",
             "kDoubleSci",
             "kChar",
             "kString",
             "kBBool",
             "kBInt16",
             "kBInt32",
             "kBFloat",
             "kBDouble",
             "kBChar",
             "kEscString"]

class Test:

    def __init__(self):
        
        self.test_set = []

    def compare(self,a,b):

        return a == b

    def print_results(self,sent_value,received_value,status):
        print(" .... {:20} --> {:20} : {:20}".format(sent_value,received_value,status))

class BoolTest(Test):
    """
    Class for testing bool ping pong.
    """

    def __init__(self):

        self.test_set = [0,1,True,False]

class IntTest(Test):
    """
    Class for testing int ping pong.
    """
   
    def __init__(self):
        
        self.test_set = [0]
        self.test_set.extend([2**i - 1 for i in range(1,40)])
        self.test_set.extend([-2**i for i in range(1,40)])
        self.test_set.sort()

class LongTest(Test):
    """
    Class for testing long ping pong.
    """
    
    def __init__(self):
 
        self.test_set = [0]
        self.test_set.extend([2**i-1 for i in range(1,40)])
        self.test_set.extend([-2**i for i in range(1,40)])
        self.test_set.sort()

class FloatTest(Test):
    """
    Class for testing float ping pong.
    """

    def __init__(self,tolerance=0.001):

        self.tolerance = tolerance

        self.test_set = [0]
        self.test_set.extend([(10.0)**e for e in range(-40,41,2)])
        self.test_set.extend([-(10.0)**e for e in range(-40,41,2)])
        self.test_set.extend([random.random() for i in range(10)])
        self.test_set.sort()
        

    def compare(self,a,b):
        """
        Make comparison with a tolerance as there will certainly be rounding
        error.
        """

        try:
            if a == 0:
                if abs(a - b) < self.tolerance:
                    return True
                else:
                    return False
            else:
                return abs(1 - b/a) < self.tolerance

        except TypeError:
            return False

    def print_results(self,sent_value,received_value,status):
        try:
            print(" .... {:20.5e} --> {:20.5e} : {:20}".format(sent_value,received_value,status))
        except ValueError:
            print(" .... {:20} --> {:20} : {:20}".format(sent_value,received_value,status))

class CharTest(Test):
    """
    Class for testing char ping pong.
    """

    def __init__(self):

        self.test_set = []
        self.test_set.extend([c for c in string.printable])
        self.test_set.append(":")

    def print_results(self,sent_value,received_value,status):
        try:
            print(b" .... " + sent_value.encode("raw-unicode-escape") + b' --> ' + received_value.encode("raw-unicode-escape") + b' : ' + status.encode("ascii"))
        except:
            print(" .... {:20} --> {:20} : {:20}".format(sent_value,received_value,status))

class StringTest(Test):
    """
    Class for testing string ping pong.
    """

    def __init__(self):

        self.test_set = ["",
                        "Test string",
                        "Test string, no escape",
                        "Test string/, with escape",
                        "Test string; no escape",
                        "Test string/; with escape",
                        "Test string,;, no escape",
                        "Test string/,/;/, with escape"]

    def print_results(self,sent_value,received_value,status):
        print(" .... {:40} --> {:40} : {:40}".format(sent_value,received_value,status))

class MultiTest(Test):
    """
    Class for testing multi value ping pong.
    """

    def __init__(self):
      
        self.int_test = IntTest()
        self.float_test = FloatTest()
 
        int_values = self.int_test.test_set 
        float_values = self.float_test.test_set 
           
        self.test_set = [[0,0,0.0]]      
        for i in range(50):
            self.test_set.append([random.choice(range(-30000,30000,500)),
                                  random.choice(range(-10000000,10000000,500)),
                                  random.choice([r*1.0 for r in range(-10000000,10000000,500)])])
           
        self.test_set.append([-40000,0,0.0])
        self.test_set.append([0,2**40,0.0])
        self.test_set.append([0,0,10.0**40])
 
    def compare(self,a,b):
    
        one_test = self.int_test.compare(a[0],b[0])
        two_test = self.int_test.compare(a[1],b[1])
        three_test = self.int_test.compare(a[2],b[2])



        return bool(one_test*two_test*three_test)
       
 
    def print_results(self,sent_value,received_value,status):

        a = sent_value
        b = received_value

        try:
            print(" .... ({},{},{:.5e}) --> ({},{},{:.5e}): {:40}".format(a[0],a[1],a[2],
                                                                          b[0],b[1],b[2],
                                                                          status))
        except:
            print(" .... {} --> {}: {:40}".format(sent_value,received_value,status))


class PingPong:
    """
    Class for running a kValuePing -> kValuePong tests of the CmdMessenger 
    library running on an arduino.
    """
 
    def __init__(self,type_name,board,test_class,command="kValuePing",delay=0.1):
        """
        Initialize class. 

            type_name: type to test.  Something like kBBool (binary boolean).
                       see TYPE_LIST for possibilities.

            board: instance of ArduinoBoard class initialized with correct
                   baud rate etc.

            test_class: instance of Test class (or derivative) that describes
                        what tests to run and what success means.

            command: command in COMMAND_NAMES to test

            delay: time between send and recieve (seconds)
        """
    
        self.type_name = type_name
        self.connection = PyCmdMessenger.CmdMessenger(board_instance=board,
                                                      command_names=COMMAND_NAMES,
                                                      warnings=False)
        self.test_class = test_class
        self.command = command
        self.delay = delay

        # Let system settle
        time.sleep(1)

        # Check connection
        self.connection.send("kAreYouReady")
 
        # Clear welcome message etc. from buffer
        i = 0
        success = False
        while i < 3:
            value = self.connection.receive()
            time.sleep(0.2)
            if value != None:
                success = True
            i += 1
      
        # Make sure we're connected 
        if not success:
            err = "Could not connect."
            raise Exception(err)

        # Figure out what the type id will be to pass to arduino (this is an 
        # integer determined by the enumeration over TYPE_LIST in the arduino
        # sketch) 
        self.type_dict = dict([(k,i) for i, k in enumerate(TYPE_LIST)])

        if self.type_name == "multivalue":
            self._type = "multivalue"
        else:
            self._type = self.type_dict[self.type_name]


    def run_tests(self,send_arg_formats=None,receive_arg_formats=None):
        """
        """

        print("------------------------------------------------------------------")
        print("Testing ping-pong for {}.".format(self.type_name))
  
        success_dict = {True:"PASS",False:"FAIL"}
    
        success_list = [] 
        for i, e in enumerate(self.test_class.test_set):

            try:

                if self._type == "multivalue":
                    self.connection.send(self.command,*e,arg_formats=send_arg_formats)
                else:
                    self.connection.send(self.command,self._type,e,arg_formats=send_arg_formats)

                v_raw = self.connection.receive(arg_formats=receive_arg_formats)

                if v_raw == None:
                    success = False
                else:

                    if self._type == "multivalue":
                        v = v_raw[1]
                    else:
                        v = v_raw[1][0]

                    success = self.test_class.compare(e,v)

            except OverflowError:
                v = "caught overflow"
                success = True

            #except:
            #    v = "exception"
            #    success = False
   
            # purge buffer in case message fragment still there
            if not success:
                self.connection.send("kAreYouReady")
                self.connection.receive()
                self.connection.receive()

            success_list.append(success) 

            self.test_class.print_results(e,v,success_dict[success])

      
        print("Passed {} of {} ping-pong tests for {}.".format(sum(success_list),
                                                               len(success_list),
                                                               self.type_name))

        print("------------------------------------------------------------------")
        print()

        return success_list


def main(argv=None):
    """
    Parse command line and run tests.
    """

    if argv == None:
        argv = sys.argv[1:]

    # Parse command line
    try:
        serial_device = argv[0]
    except IndexError:
        err = "Incorrect arguments. Usage: \n\n{}\n\n".format(__usage__)
        raise IndexError(err)

    # Create an arduino board instance with a serial connection
    board = PyCmdMessenger.ArduinoBoard(serial_device,baud_rate=BAUD_RATE,timeout=0.1)

    # Create a series of test instances
    bool_test = BoolTest()
    int_test = IntTest()
    long_test = LongTest()
    float_test = FloatTest()
    char_test = CharTest()
    string_test = StringTest()
    multi_test = MultiTest()

    print("******************************************************************")
    print("*    Test using binary interface (should have 100% success)      *")
    print("******************************************************************")

    binary_trials = []
    t = PingPong("multivalue",board,multi_test,command="kMultiValuePing")
    binary_trials.extend(t.run_tests(send_arg_formats="ilf",receive_arg_formats="ilf"))

    t = PingPong("kBBool",board,bool_test)
    binary_trials.extend(t.run_tests(send_arg_formats="g?",receive_arg_formats="?"))

    t = PingPong("kChar",board,char_test)
    binary_trials.extend(t.run_tests(send_arg_formats="gc",receive_arg_formats="c"))
    
    t = PingPong("kBInt16",board,int_test)
    binary_trials.extend(t.run_tests(send_arg_formats="gi",receive_arg_formats="i"))

    t = PingPong("kBInt32",board,int_test)
    binary_trials.extend(t.run_tests(send_arg_formats="gl",receive_arg_formats="l"))

    t = PingPong("kBFloat",board,float_test)
    binary_trials.extend(t.run_tests(send_arg_formats="gf",receive_arg_formats="f"))

    t = PingPong("kBDouble",board,float_test)
    binary_trials.extend(t.run_tests(send_arg_formats="gd",receive_arg_formats="d"))

    t = PingPong("kString",board,string_test)
    binary_trials.extend(t.run_tests(send_arg_formats="gs",receive_arg_formats="s"))
    
    t = PingPong("kEscString",board,string_test)
    binary_trials.extend(t.run_tests(send_arg_formats="gs",receive_arg_formats="s"))


    
    print("SUMMARY: Passed {} of {} binary interface binary_trials".format(sum(binary_trials),
                                                                    len(binary_trials)))
    print()

    print("******************************************************************")
    print("*     Test using string interface (will fail a lot)              *")
    print("******************************************************************")

    string_trials = []

    t = PingPong("kBool",board,bool_test)
    string_trials.extend(t.run_tests())

    t = PingPong("kChar",board,char_test)
    string_trials.extend(t.run_tests())
    
    t = PingPong("kInt16",board,int_test)
    string_trials.extend(t.run_tests())

    t = PingPong("kInt32",board,int_test)
    string_trials.extend(t.run_tests())
     
    t = PingPong("kFloat",board,float_test)
    string_trials.extend(t.run_tests())

    t = PingPong("kFloatSci",board,float_test)
    string_trials.extend(t.run_tests())
    
    t = PingPong("kDouble",board,float_test)
    string_trials.extend(t.run_tests())

    t = PingPong("kDoubleSci",board,float_test)
    string_trials.extend(t.run_tests())

    t = PingPong("kString",board,string_test)
    string_trials.extend(t.run_tests())
    
    t = PingPong("kEscString",board,string_test)
    string_trials.extend(t.run_tests())
    
    print("SUMMARY: Passed {} of {} string interface string_trials".format(sum(string_trials),
                                                                    len(string_trials)))
    print()

    print("******************************************************************")
    print("*                   FINAL SUMMARY                                *")
    print("******************************************************************")

    print()
    print("SUMMARY: Passed {} of {} binary interface binary_trials".format(sum(binary_trials),
                                                                    len(binary_trials)))
    print()
    print("SUMMARY: Passed {} of {} string interface string_trials".format(sum(string_trials),
                                                                    len(string_trials)))
    print()
    

if __name__ == "__main__":
    main()
