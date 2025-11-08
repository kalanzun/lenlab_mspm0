#ifndef VOLT_H
#define VOLT_H

#include "packet.h"

#include "ti/devices/msp/peripherals/hw_adc12.h"

struct ADC {
    const uint8_t index;
    ADC12_Regs* const adc12;
    const uint8_t chan_id;

    volatile bool done;
};

struct Waveform { // oscilloscope
    struct Packet packet;
    uint32_t payload[2][8][432]; // two samples per uint32_t
};

struct Points { // logging
    struct Packet packet;
    uint32_t payload[1024]; // two values per uint32_t
};

struct Volt {
    union {
        struct Waveform wave;
        struct Points points[2];
    };

    struct ADC adc[2];

    uint16_t block_count;
    uint16_t block_write;

    uint16_t ping_pong;
    uint16_t point_index;
    uint16_t point_reset;
};

extern struct Volt volt;

void volt_init(void);

void volt_startLogging(uint32_t interval);

void volt_getPoints(uint32_t polling);

void volt_createLoggingExampleData(uint32_t interval);

void volt_acquireWaveform(uint8_t code, uint16_t interval, uint16_t offset);

#endif
