#ifndef MEMORY_H
#define MEMORY_H

#include "packet.h"

#define KB 1024

struct Memory {
    struct Packet packet;
    uint8_t payload[28 * KB - sizeof(struct Packet)];
};

static_assert(sizeof(struct Memory) == 28 * KB,
    "sizeof struct Memory is not 28 kilobytes");

extern struct Memory memory;

#endif
