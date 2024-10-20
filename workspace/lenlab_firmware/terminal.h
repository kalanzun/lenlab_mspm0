#ifndef TERMINAL_H
#define TERMINAL_H

#include <stdbool.h>
#include <stdint.h>

#include "packet.h"

struct Terminal {
    Packet cmd;
    Packet rpl;
    volatile bool rx_flag;
    volatile bool tx_flag;
};

extern struct Terminal terminal;

void terminal_receiveCommand(void);

void terminal_transmitPacket(const Packet *packet);

void terminal_transmitReply(void);

void terminal_init(void);

void terminal_tick(void);

void terminal_main(void);

#endif
