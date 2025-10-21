#include "adc.h"

#include "ti_msp_dl_config.h"

struct ADC adc[2] = {
    {
        .adc12 = ADC12_CH1_INST,
        .chan_id = DMA_CH1_CHAN_ID,
        .index = 0,
    },
    {
        .adc12 = ADC12_CH2_INST,
        .chan_id = DMA_CH2_CHAN_ID,
        .index = 1,
    },
};

void adc_init(void)
{
    NVIC_EnableIRQ(ADC12_CH1_INST_INT_IRQN);
    NVIC_EnableIRQ(ADC12_CH2_INST_INT_IRQN);
}

void adc_reconfigureOsci(struct ADC * const self)
{
    DL_ADC12_disableConversions(self->adc12);

    // FIFO
    // DMA
    DL_ADC12_enableFIFO(self->adc12);
    DL_ADC12_enableDMA(self->adc12);

    // Event Subscriber Channel ID
    // channel 12 OSCI_DELAY
    DL_ADC12_setSubscriberChanID(self->adc12, 12);
    
    /* Enable ADC12 interrupt */
    DL_ADC12_disableInterrupt(self->adc12, DL_ADC12_INTERRUPT_MEM0_RESULT_LOADED);

    DL_ADC12_clearInterruptStatus(self->adc12, DL_ADC12_INTERRUPT_DMA_DONE);
    DL_ADC12_enableInterrupt(self->adc12, DL_ADC12_INTERRUPT_DMA_DONE);

    DL_ADC12_enableConversions(self->adc12);
}

void adc_reconfigureVolt(struct ADC * const self)
{
    DL_ADC12_disableConversions(self->adc12);

    // FIFO
    // DMA
    DL_ADC12_disableFIFO(self->adc12);
    DL_ADC12_disableDMA(self->adc12);

    // Event Subscriber Channel ID
    // channel 13 VOLT_TIMER
    DL_ADC12_setSubscriberChanID(self->adc12, 13);
    
    /* Enable ADC12 interrupt */
    DL_ADC12_disableInterrupt(self->adc12, DL_ADC12_INTERRUPT_DMA_DONE);

    DL_ADC12_clearInterruptStatus(self->adc12, DL_ADC12_INTERRUPT_MEM0_RESULT_LOADED);
    DL_ADC12_enableInterrupt(self->adc12, DL_ADC12_INTERRUPT_MEM0_RESULT_LOADED);

    DL_ADC12_enableConversions(self->adc12);
}

void adc_restart(struct ADC * const self)
{
    self->done = false;
}

uint16_t adc_getResult(struct ADC * const self)
{
    return DL_ADC12_getMemResult(self->adc12, DL_ADC12_MEM_IDX_0);    
}

static void adc_callback(struct ADC *const self, struct ADC *const other)
{
    switch (DL_ADC12_getPendingInterrupt(self->adc12)) {
    case DL_ADC12_IIDX_DMA_DONE:
        self->done = true;
        if (other->done) osci_callback();
        break;
    case DL_ADC12_IIDX_MEM0_RESULT_LOADED:
        self->done = true;
        if (other->done) volt_callback();
        break;
    default:
        break;
    }
}

void ADC12_CH1_INST_IRQHandler(void)
{
    adc_callback(&adc[0], &adc[1]);
}

void ADC12_CH2_INST_IRQHandler(void)
{
    adc_callback(&adc[1], &adc[0]);
}
