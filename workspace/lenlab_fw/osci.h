#ifndef OSCI_H
#define OSCI_H

#include "packet.h"

#include "ti/devices/msp/peripherals/hw_adc12.h"


struct Channel {
    const uint8_t index;
    ADC12_Regs* const adc12;
    const uint8_t chan_id;

    bool done;
    uint16_t block_count;
    uint16_t block_write;
};

struct Osci {
    struct Packet packet;
    uint32_t payload[2][8][432]; // two samples per uint32_t
    struct Channel channel[2];
};

extern struct Osci osci;

void osci_init(void);

void osci_acquire(uint8_t code, uint16_t interval, uint16_t offset);

#endif
