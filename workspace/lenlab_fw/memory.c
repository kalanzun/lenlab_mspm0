#include "memory.h"
#include "ti/driverlib/dl_crc.h"

struct Memory memory = { .packet = { .label = 'L', .code = 'm', .length = sizeof(struct Memory), .argument = { '2', '8', 'K', 'B' } } };

void memory_init(void)
{
    uint32_t* payload = (uint32_t*)&memory.payload;

    for (uint32_t i = 0; i < sizeof(memory.payload) / sizeof(*payload); i++) {
        DL_CRC_feedData32(CRC, 0);
        payload[i] = DL_CRC_getResult32(CRC);
    }
}