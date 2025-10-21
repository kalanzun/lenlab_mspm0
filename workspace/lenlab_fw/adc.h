#ifndef ADC_H
#define ADC_H

#include <stdbool.h>
#include <stdint.h>

#include "ti/devices/msp/peripherals/hw_adc12.h"

struct ADC {
    ADC12_Regs* const adc12;
    const uint8_t chan_id;
    const uint8_t index;
    volatile bool done;
};

extern struct ADC adc[2];

void adc_init(void);

void adc_reconfigureOsci(struct ADC * const self);

void adc_reconfigureVolt(struct ADC * const self);

void adc_restart(struct ADC * const self);

uint16_t adc_getResult(struct ADC * const self);

void osci_callback(void);

void volt_callback(void);

#endif
