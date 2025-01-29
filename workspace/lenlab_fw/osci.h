#ifndef OSCI_H
#define OSCI_H

#include "packet.h"

struct OsciChannel {
    uint32_t payload[3 * 1024]; // two samples per uint32_t
};

struct Osci {
    struct Packet packet;
    struct OsciChannel channel[2];
    volatile bool ch1_done;
    volatile bool ch2_done;
};

extern struct Osci osci;

void osci_init(void);

void osci_acquire(uint8_t code, uint32_t interval);

#endif
