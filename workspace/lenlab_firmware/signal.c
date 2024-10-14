#include "signal.h"

#include "ti_msp_dl_config.h"

typedef int32_t sq16_t;

const sq16_t attenuation = 81344; // 4096 / 3300 mV * (1 << 16)

void signal_constant(int32_t amplitude_mV)
{
    sq16_t amplitude = attenuation * amplitude_mV;
    uint16_t *ptr = (uint16_t *) &amplitude;
    DL_DAC12_output12(DAC0, ptr[1]);
}

void signal_init(void)
{
    signal_constant(0);
    DL_DAC12_enable(DAC0);
}
