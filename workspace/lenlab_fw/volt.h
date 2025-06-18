#ifndef VOLT_H
#define VOLT_H

#include "packet.h"

struct VoltPoint {
    uint32_t time;
    uint16_t ch[2];
};

struct VoltReply {
    struct Packet packet;
    struct VoltPoint points[4];
};

struct Volt {
    struct VoltReply reply[2];
    bool ping_pong;
    uint8_t point_index;
    uint32_t interval;
    uint32_t time;
};

void volt_start(uint32_t interval);

void volt_next(void);

void volt_stop(void);

#endif
