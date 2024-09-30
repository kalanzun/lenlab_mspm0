#ifndef TERMINAL_H
#define TERMINAL_H

#include <stdbool.h>
#include <stdint.h>

struct Packet {
    uint8_t ack;
    uint8_t code;
    uint16_t length;
    uint8_t arg0;
    uint8_t arg1;
    uint8_t arg2;
    uint8_t arg3;
};

struct Terminal {
    volatile bool rx_flag;
    volatile bool tx_flag;
    volatile struct Packet cmd;
    struct Packet rpl;
};

extern struct Terminal terminal;

void terminal_transmit(void);

void terminal_receive(void);

void terminal_init(void);

#endif
