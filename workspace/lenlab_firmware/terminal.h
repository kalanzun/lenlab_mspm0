#ifndef TERMINAL_H
#define TERMINAL_H

#include <stdbool.h>
#include <stdint.h>

struct Packet {
    uint8_t ack;
    uint8_t code;
    uint16_t length;
    union {
        uint8_t bytes[4];
        uint32_t uint32;
        int32_t int32;
    } arg;
};

struct Terminal {
    volatile bool rx_flag;
    volatile bool ld_flag;
    volatile bool tx_flag;
    volatile struct Packet cmd;
    volatile uint8_t payload[32];
    struct Packet rpl;
};

extern struct Terminal terminal;

void terminal_transmit(void);

void terminal_receive(void);

void terminal_init(void);

#endif
