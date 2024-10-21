#include "memory.h"

Memory memory = { .packet = { .label = 'L', .length = sizeof(((Memory*)0)->values), .key = 'm', .payload = { '3', '0', 'K', 'B' } } };

void memory_init(void)
{
    for (uint16_t i = 0; i < sizeof(memory) / 2; i++) {
        memory.values[i] = i;
    }
}
