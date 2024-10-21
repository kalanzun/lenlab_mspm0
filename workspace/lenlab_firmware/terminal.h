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
    volatile bool rx_stalled;
};

extern struct Terminal terminal;

void terminal_receiveCommand(void);

void terminal_transmitPacket(const Packet* packet);

void terminal_transmitReply(void);

enum Baudrate {
    Baudrate_9600,
    Baudrate_4MBd,
};

void terminal_changeBaudrate(enum Baudrate baudrate);

void terminal_init(void);

void terminal_main(void);

void terminal_tick(void);

#endif
