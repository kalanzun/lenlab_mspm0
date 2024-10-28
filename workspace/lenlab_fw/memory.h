#ifndef MEMORY_H
#define MEMORY_H

#include "packet.h"

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#define KB 1024

struct Memory {
    struct Packet packet;
    uint8_t payload[28 * KB - sizeof(struct Packet)];
};

static_assert(sizeof(struct Memory) == 28 * KB,
    "sizeof struct Memory is not 28 KB");

extern struct Memory memory;

void memory_init(void);

#endif
