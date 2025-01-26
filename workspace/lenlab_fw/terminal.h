#ifndef TERMINAL_H
#define TERMINAL_H

#include "packet.h"

struct Terminal {
    struct Packet cmd;
    uint16_t payload[4];
    struct Packet rpl;
    volatile bool rx_flag;
    volatile bool tx_flag;
    volatile bool rx_stalled;
};

extern struct Terminal terminal;

void terminal_receiveCommand(void);

void terminal_transmitPacket(const struct Packet* packet);

void terminal_sendReply(uint8_t code, uint32_t arg);

void terminal_init(void);

void terminal_tick(void);

#endif
