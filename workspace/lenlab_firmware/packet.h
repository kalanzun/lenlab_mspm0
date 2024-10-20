#ifndef PACKET_H
#define PACKET_H

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

typedef union {
    uint8_t buffer[8];
    struct {
        uint8_t label;
        uint8_t key;
        uint16_t length;
        uint8_t payload[4];
    };
} Packet;

static_assert(sizeof(Packet) == sizeof(((Packet *) 0)->buffer), "sizeof Packet does not equal sizeof buffer");

static inline bool packet_comparePayload(const Packet *restrict self, const Packet *restrict other)
{
    for (uint8_t i = 0; i < sizeof(self->payload); i++)
        if (self->payload[i] != other->payload[i])
            return false;

    return true;
}

static inline bool packet_comparePacket(const Packet *restrict self, const Packet *restrict other)
{
    for (uint8_t i = 0; i < sizeof(self->buffer); i++)
        if (self->buffer[i] != other->buffer[i])
            return false;

    return true;
}

static inline void packet_copyPayload(Packet *restrict self, const Packet *restrict other)
{
    for (uint8_t i = 0; i < sizeof(self->payload); i++)
        self->payload[i] = other->payload[i];
}

static inline void packet_copyPacket(Packet *restrict self, const Packet *restrict other)
{
    for (uint8_t i = 0; i < sizeof(self->buffer); i++)
        self->buffer[i] = other->buffer[i];
}

#endif
