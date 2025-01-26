#ifndef PACKET_H
#define PACKET_H

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

struct Packet {
    uint8_t label;
    uint8_t code;
    uint16_t length;
    uint32_t arg;
};

static_assert(sizeof(struct Packet) == 8,
    "sizeof struct Packet is not 8 bytes");

#define LENGTH(_array) (sizeof(_array) / sizeof(*(_array)))

#define ARG_STR(_x) ((_x[0]) + ((_x[1]) << 8) + ((_x[2]) << 16) + ((_x[3]) << 24))

#endif
