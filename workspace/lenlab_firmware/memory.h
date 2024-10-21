#ifndef MEMORY_H
#define MEMORY_H

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#include "packet.h"

#define KB 1024

typedef union {
    uint8_t buffer[8 + 2 * 15 * KB];
    struct {
        Packet packet;
        uint16_t values[15 * KB];
    };
} Memory;

static_assert(sizeof(Memory) == sizeof(((Memory*)0)->buffer),
    "sizeof Memory does not equal sizeof buffer");

extern Memory memory;

void memory_init(void);

#endif
