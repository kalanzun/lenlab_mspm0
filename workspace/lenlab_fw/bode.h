#ifndef BODE_H
#define BODE_H

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

struct Bode {
    uint16_t interval;

    uint8_t countdown;
};

extern struct Bode bode;

void bode_start(uint32_t sample_rate, uint16_t length, uint16_t amplitude, uint16_t interval);

void bode_tick(void);

#endif
