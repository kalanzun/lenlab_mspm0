#include "signal.h"

#include "q.h"

#include "ti_msp_dl_config.h"

const q_t attenuation = 81344; // 4096 / 3300 mV * (1 << 16)

void signal_constant(int32_t amplitude_mV)
{
    q_t amplitude = attenuation * amplitude_mV;
    DL_DAC12_output12(DAC0, q_integer_part(amplitude));
}

void signal_init(void)
{
    signal_constant(-1650);
    DL_DAC12_enable(DAC0);
}
