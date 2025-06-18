#ifndef ADC_H
#define ADC_H

#include <stdbool.h>
#include <stdint.h>

#include "ti/devices/msp/peripherals/hw_adc12.h"

struct ADC {
    const uint8_t index;
    ADC12_Regs* const adc12;
    bool done;
};

extern struct ADC adc[2];

void adc_init(void);

void adc_reconfigureOsci(struct ADC * const self);

void adc_reconfigureVolt(struct ADC * const self);

void osci_handler(void);

void volt_handler(void);

#endif
