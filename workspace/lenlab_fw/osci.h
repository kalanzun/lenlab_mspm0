#ifndef OSCI_H
#define OSCI_H

#include "packet.h"

struct Channel {
    volatile bool done;
    volatile uint16_t block_count;
    volatile uint16_t block_write;
};

struct Osci {
    struct Packet packet;
    uint32_t payload[2][8][384]; // two samples per uint32_t
    volatile struct Channel channel[2];
};

extern struct Osci osci;

void osci_init(void);

void osci_acquire(uint8_t code, uint32_t interval);

#endif
