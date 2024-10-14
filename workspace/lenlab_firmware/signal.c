#include "signal.h"

#include "ti_msp_dl_config.h"

typedef int32_t sq16_t;

const sq16_t attenuation = 81344; // 4096 / 3300 mV * (1 << 16)

union number {
    sq16_t q;
    struct {
        uint16_t lo;
        uint16_t hi;
    }; // little endian
};

void signal_constant(int32_t amplitude_mV)
{
    union number amplitude;

    amplitude.q = attenuation * amplitude_mV;
    DL_DAC12_output12(DAC0, amplitude.hi);
}

void signal_init(void)
{
    signal_constant(0);
    DL_DAC12_enable(DAC0);
}
