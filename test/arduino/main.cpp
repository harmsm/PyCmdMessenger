/* -----------------------------------------------------------------------------
 * Test .ino file to verify PyCmdMessenger functionality.  Should be compiled
 * with CmdMessenger.h and CmdMessenger.cpp in the sketch directory, then 
 * loaded onto the arduino prior to running run_test.py from the 
 * PyCmdMessenger/test/run_tests.py script.
 *----------------------------------------------------------------------------*/

#include "CmdMessenger.h"
#include <stdlib.h>

// ---------------------------------------------------------------------------------------
// direct lift from here
// https://arduino.stackexchange.com/questions/3079/how-to-retrieve-the-data-type-of-a-variable

// Generic catch-all implementation.
template <typename T_ty> struct TypeInfo { static const char * name; };
template <typename T_ty> const char * TypeInfo<T_ty>::name = "unknown";

// Handy macro to make querying stuff easier.
#define TYPE_NAME(var) TypeInfo< typeof(var) >::name

// Handy macro to make defining stuff easier.
#define MAKE_TYPE_INFO(type)  template <> const char * TypeInfo<type>::name = #type;

// Type-specific implementations.
MAKE_TYPE_INFO( int )
MAKE_TYPE_INFO( float )
MAKE_TYPE_INFO( double )
MAKE_TYPE_INFO( short )
// ------------------------------------ ---------------------------------------------------

#define HACK_BUFFER_SIZE 128

void dbl_to_sci(char *out_string, double number, int num_decimal_places){

    /* Generate a string representing a double in scientific notation with
     * num_decimal_places digits after the decmial place.  
     *
     * Arguments:
     *     out_string is a char buffer that will hold the string. 
     *     number is the number to be processed.
     *     num_decimal_places is the number of decimal places to show.
     *
     * Basic function form was derived from discussion here:
     *     http://forum.arduino.cc/index.php?topic=166041.msg1241170#msg1241170
     */ 

    int maximum_indiv_message_size = HACK_BUFFER_SIZE;


    /* The pieces we're going to build */
    char sign, exponent_sign;
    unsigned long before_decimal, after_decimal, exponent;

    /* Deal with NaN */ 
    if (isnan(number)) {
        sprintf(out_string,"nan");
        return;
    }

    /* Deal with infinity */
    if (isinf(number)) { 

        if (number < 0) {
            sign = '-';
        } else { 
            sign = ' ';
        }

        sprintf(out_string,"%s%s",sign,"inf");
        return;
        
    }
  
    /* Figure out what to do with the sign */
    sign = ' ';
    if (number < 0.0) {
        sign = '-';
        number = -number;
    }

    /* --- At this point, the number should be a positive float --- */
  
    /* Discover the proper exponent */

    /* Large number */
    exponent = 0;
    while (number >= 10.0) {
        number /= 10.0;
        exponent++;
    }

    /* Small number */
    if (number != 0) {
        while (number < 1.0) {
            number *= 10.0;
            exponent--;
        }
    }
    
    /* Decide on exponent sign */ 
    if (exponent >= 0) {
        exponent_sign = '+';
    } else { 
        exponent_sign = '-';
        exponent = -1*exponent;
    }
    
    /* --- At this point, the number is a positive float between 1 and 10 --- */

    /* Add an offset so this will round to the correct number of digits when we 
     * grab num_decimal_places off the end. */
    double rounding = 0.5;
    for (int i = 0; i < num_decimal_places; ++i) {
        rounding /= 10.0;
    }
    number += rounding;

    /* Extract the part of the number before the decimal */
    before_decimal = (unsigned long)number;

    /* Turn the part of the number after the decimal into a num_decimal_places
     * long integer */
    double remainder = number - (double)before_decimal;
    for (int i = 0; i < num_decimal_places; i++){
        remainder *= 10;
    }    
    after_decimal = (unsigned long)remainder;

    /* Create the formatted output string, only printing decimal point if 
       there are digits there to show. */
    if (num_decimal_places > 0) { 
        vsnprintf(out_string,"%c%i.%iE%c%i",sign,before_decimal,after_decimal,exponent_sign,exponent);
    } else {
        vsnprintf(out_string,   "%c%iE%c%i",sign,before_decimal,              exponent_sign,exponent);
    }

}


const int BAUD_RATE = 9600;
CmdMessenger c = CmdMessenger(Serial,',',';','/');

/* Define available CmdMessenger commands */
enum {
    send_string,
    send_float,
    send_int,
    send_two_int,
    receive_string,
    receive_float,
    receive_int,
    receive_two_int,
    result,
    error,
};

void on_unknown_command(void){
    c.sendCmd(error,"Command without callback.");
}

void on_send_string(void){
    c.sendCmd(result,"A string with /, and /; escape");
}

void on_send_float(void){
    c.sendCmd(result,99.9);
}

void on_send_int(void){
    c.sendCmd(result,-10);
}

void on_send_two_int(void){

    int i;

    c.sendCmdStart(result);
    c.sendCmdArg(-10);
    c.sendCmdArg(10);
    c.sendCmdEnd();

}

void on_receive_string(void){
    char * value = c.readStringArg();
    c.sendCmd(result,"got it!");
}

void on_receive_float(void){

    float value = c.readFloatArg();

    char junk[HACK_BUFFER_SIZE];
    float_to_sci(junk, value, 10);

    if (TYPE_NAME(value) == "float"){
        //c.sendCmd(result,10*value);
    }

    //sprintf(junk,"%s %s","abc","def");
    c.sendCmd(result,junk);


    //c.sendCmd(result,TYPE_NAME(value) );
         
    //c.sendCmd(result,value*10.0);

}

void on_receive_int(void){
    int value = c.readInt16Arg();
    c.sendCmd(result,value*10);
}

void on_receive_two_int(void){

    int value1 = c.readInt16Arg();
    int value2 = c.readInt16Arg();

    c.sendCmdStart(result);
    c.sendCmdArg(10*value1);
    c.sendCmdArg(10*value2);
    c.sendCmdEnd();

}

/* Define callbacks for CmdMessenger commands */
void attach_callbacks(void) { 
  
    // Attach callback methods
    c.attach(on_unknown_command);

    c.attach(send_string,on_send_string);
    c.attach(send_float,on_send_float);
    c.attach(send_int,on_send_int);
    c.attach(send_two_int,on_send_two_int);

    c.attach(receive_string,on_receive_string);
    c.attach(receive_float,on_receive_float);
    c.attach(receive_int,on_receive_int);
    c.attach(receive_two_int,on_receive_two_int);

}

void setup() {
    Serial.begin(BAUD_RATE);
    c.printLfCr();  // <-- This is critical, as python library assumes newlines
    attach_callbacks();    
}

void loop() {
    c.feedinSerialData();
}
