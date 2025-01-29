#include "bode.h"

#include "osci.h"
#include "signal.h"

struct Bode bode = { .countdown = 0 };

void bode_start(uint32_t sample_rate, uint16_t length, uint16_t amplitude, uint16_t interval)
{
    struct Bode* const self = &bode;

    signal_sinus(sample_rate, length, amplitude, 0, 0);

    self->countdown = 2;
    self->interval = interval;
}

void bode_tick(void)
{
    struct Bode* const self = &bode;

    if (self->countdown == 2) {
        self->countdown = 1;
    } else if (self->countdown) {
        self->countdown = 0;
        osci_acquire('b', self->interval);
    }
}