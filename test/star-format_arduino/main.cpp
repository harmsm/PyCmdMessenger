#include "CmdMessenger.h"  

CmdMessenger c = CmdMessenger(Serial, ',',';','/');

enum
{
    multi_ping,        // expects three doubles
    multi_pong,        // returns three doubles
};

void on_multi_ping(void){

    int i;
    double value;
    long random_number, trimmed_random;

    random_number = random(1,15);
    trimmed_random = random_number;

    c.sendCmdStart(multi_pong);
    for (i = 0; i < random_number; i++){
        c.sendCmdBinArg(trimmed_random);
        trimmed_random = trimmed_random - 1;
    }
    c.sendCmdEnd();

}


void attach_callbacks()
{
  c.attach(multi_ping, on_multi_ping);
}

void setup() 
{
  Serial.begin(115200); 
  randomSeed(analogRead(0));
  attach_callbacks();
}

void loop() 
{
  c.feedinSerialData();
}

