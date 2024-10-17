#ifndef TERMINAL_H
#define TERMINAL_H

#include <stdbool.h>
#include <stdint.h>

struct Packet {
    uint8_t buffer[8];
};

#define PACKET_SIZE (sizeof(((struct Packet *) 0)->buffer))

struct Terminal {
    struct Packet cmd;
    struct Packet rpl;
    uint16_t remember;
    uint16_t flushes;
    uint32_t spurious;
    uint8_t baudrate_reply;
};

void terminal_init(void);

void terminal_tick(void);

void terminal_main(void);

#endif
