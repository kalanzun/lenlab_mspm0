#ifndef Q_H
#define Q_H

#include <stdbool.h>
#include <stdint.h>

// fixed point signed integer
// 16 bit signed integer part, 16 bit fractional part
// TI notation: SQ15.16
// Arm notation: Q16.16
typedef int32_t q_t;

static inline int16_t q_integer_part(q_t value)
{
    return ((int16_t *) &value)[1]; // little endian
}

#endif
