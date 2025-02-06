#ifndef SIGNAL_H
#define SIGNAL_H

#include "packet.h"

struct Signal {
    struct Packet packet;
    uint16_t payload[2000];

    uint16_t length;
};

extern struct Signal signal;

void signal_init(void);

void signal_sinus(uint16_t length, uint16_t amplitude, uint16_t multiplier, uint16_t harmonic);

#endif
