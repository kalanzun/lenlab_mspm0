#ifndef OSCI_H
#define OSCI_H

#include "adc.h"
#include "packet.h"

struct OsciChannel {
    const uint8_t index;
    const uint8_t chan_id;

    uint16_t block_count;
    uint16_t block_write;
};

struct Osci {
    struct Packet packet;
    uint32_t payload[2][8][432]; // two samples per uint32_t
    
    struct OsciChannel channel[2];
};

extern struct Osci osci;

void osci_init(void);

void osci_acquire(uint8_t code, uint16_t interval, uint16_t offset);

#endif
