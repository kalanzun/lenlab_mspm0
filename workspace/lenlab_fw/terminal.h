#ifndef TERMINAL_H
#define TERMINAL_H

#include "packet.h"

struct Terminal {
    struct Packet cmd;
    struct Packet rpl;
    volatile bool rx_flag;
    volatile bool tx_flag;
    volatile bool rx_stalled;
};

extern struct Terminal terminal;

void terminal_receiveCommand(void);

void terminal_transmitReply(void);

void terminal_init(void);

void terminal_tick(void);

void terminal_main(void);

#endif
