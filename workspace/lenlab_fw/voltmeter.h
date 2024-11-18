#ifndef VOLTMETER_H
#define VOLTMETER_H

#include "packet.h"

struct VoltmeterPoint {
    uint32_t time;
    uint16_t ch1;
    uint16_t ch2;
};

struct VoltmeterReply {
    struct Packet packet;
    struct VoltmeterPoint points[8];
};

enum VoltmeterFlag {
    NO_FLAG = 0,
    FLAG_ADC0 = 1,
    FLAG_ADC1 = 2,
    FLAG_BOTH = 3,
};

struct Voltmeter {
    enum VoltmeterFlag flag;
    struct VoltmeterReply reply[2];
    bool ping_pong;
    uint8_t point_index;
    uint32_t time;
};

void voltmeter_start(void);

void voltmeter_next(void);

void voltmeter_stop(void);

void voltmeter_init(void);

#endif
