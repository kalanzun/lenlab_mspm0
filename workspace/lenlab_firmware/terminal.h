#ifndef TERMINAL_H
#define TERMINAL_H

#include <stdbool.h>
#include <stdint.h>

struct Terminal {
    volatile bool rx_flag;
    volatile bool ld_flag;
    volatile bool tx_flag;
    volatile uint8_t cmd[8];
    volatile uint8_t rpl[8];
    volatile uint8_t pay[32];
};

extern struct Terminal terminal;

uint8_t terminal_getKey(void);

int32_t terminal_getArgInt32(void);

void terminal_transmit(void);

void terminal_receive(void);

void terminal_init(void);

#endif
