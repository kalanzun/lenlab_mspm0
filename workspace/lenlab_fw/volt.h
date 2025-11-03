#ifndef VOLT_H
#define VOLT_H

#include "packet.h"

#include "ti/devices/msp/peripherals/hw_adc12.h"

struct ADC {
    const uint8_t index;
    ADC12_Regs* const adc12;
    const uint8_t chan_id;

    bool done;

    uint16_t block_count;
    uint16_t block_write;
};

struct Osci { // waveform
    struct Packet packet;
    uint32_t payload[2][8][432]; // two samples per uint32_t
};

struct Points { // logging
    struct Packet packet;
    uint32_t payload[512]; // two values per uint32_t
};

struct Volt {
    union {
        struct Osci osci;
        struct Points points[2];
    };

    struct ADC adc[2];

    uint16_t ping_pong;
    uint16_t point_index;
};

extern struct Volt volt;

void volt_init(void);

void volt_startLogging(uint32_t interval);

void volt_stopLogging(void);

void volt_acquire(uint8_t code, uint16_t interval, uint16_t offset);

#endif
