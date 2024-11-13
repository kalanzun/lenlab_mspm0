#ifndef PACKET_H
#define PACKET_H

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

struct Packet {
    uint8_t label;
    uint8_t code;
    uint16_t length;
    uint8_t argument[4];
};

static_assert(sizeof(struct Packet) == 8,
    "sizeof struct Packet is not 8 bytes");

#define LENGTH(_array) (sizeof(_array) / sizeof(*(_array)))

static inline bool packet_compareArgument(const struct Packet* restrict self, const struct Packet* restrict other)
{
    for (uint8_t i = 0; i < LENGTH(self->argument); i++)
        if (self->argument[i] != other->argument[i])
            return false;

    return true;
}

static inline void packet_copyArgument(struct Packet* restrict destination, const struct Packet* restrict source)
{
    for (uint8_t i = 0; i < LENGTH(destination->argument); i++)
        destination->argument[i] = source->argument[i];
}

#endif
