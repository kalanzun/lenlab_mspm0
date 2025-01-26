#ifndef OSCI_H
#define OSCI_H

#include "packet.h"

struct OsciReply {
    struct Packet packet;
    uint32_t payload[3 * 1024]; // two samples per uint32_t
};

struct Osci {
    struct OsciReply channel[2];
    volatile bool ch1_done;
    volatile bool ch2_done;
};

extern struct Osci osci;

void osci_init(void);

void osci_acquire(uint16_t averages);

#endif
