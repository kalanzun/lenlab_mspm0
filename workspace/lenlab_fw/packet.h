#ifndef PACKET_H
#define PACKET_H

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

static const uint16_t lenlab_label = 'L' + ('l' << 8);

struct Packet {
    uint16_t label;
    uint16_t length;
    uint8_t argument[4];
};

static_assert(sizeof(struct Packet) == 8,
    "sizeof struct Packet is not 8");

#define LENGTH(_array) (sizeof(_array) / sizeof(*(_array)))

static inline bool packet_compareArgument(const struct Packet* restrict self, const struct Packet* restrict other)
{
    for (uint8_t i = 0; i < LENGTH(self->argument); i++)
        if (self->argument[i] != other->argument[i])
            return false;

    return true;
}

static inline void packet_copyArgument(struct Packet* restrict self, const struct Packet* restrict other)
{
    for (uint8_t i = 0; i < LENGTH(self->argument); i++)
        self->argument[i] = other->argument[i];
}

#endif
