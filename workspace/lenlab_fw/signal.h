#ifndef SIGNAL_H
#define SIGNAL_H

#include "packet.h"

struct Signal {
    struct Packet packet;
    uint16_t payload[2000];
    uint16_t sample_rate;
    uint16_t length;
};

extern struct Signal signal;

void signal_createSinus(uint16_t length, uint16_t amplitude);

void signal_addHarmonic(uint16_t multiplier, uint16_t amplitude);

void signal_start(uint16_t sample_rate);

void signal_stop(void);

#endif
