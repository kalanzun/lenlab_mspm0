#include "ti_msp_dl_config.h"

void adc_reconfigureOsci(ADC12_Regs* const adc12)
{
    DL_ADC12_disableConversions(adc12);

    // FIFO
    // DMA
    DL_ADC12_enableFIFO(adc12);
    DL_ADC12_enableDMA(adc12);

    // Event Subscriber Channel ID
    // channel 12 OSCI_DELAY
    DL_ADC12_setSubscriberChanID(adc12, 12);
    
    /* Enable ADC12 interrupt */
    DL_ADC12_disableInterrupt(adc12, DL_ADC12_INTERRUPT_MEM0_RESULT_LOADED);

    DL_ADC12_clearInterruptStatus(adc12, DL_ADC12_INTERRUPT_DMA_DONE);
    DL_ADC12_enableInterrupt(adc12, DL_ADC12_INTERRUPT_DMA_DONE);

    DL_ADC12_enableConversions(adc12);
}

void adc_reconfigureVolt(ADC12_Regs* const adc12)
{
    DL_ADC12_disableConversions(adc12);

    // FIFO
    // DMA
    DL_ADC12_disableFIFO(adc12);
    DL_ADC12_disableDMA(adc12);

    // Event Subscriber Channel ID
    // channel 13 VOLT_TIMER
    DL_ADC12_setSubscriberChanID(adc12, 13);
    
    /* Enable ADC12 interrupt */
    DL_ADC12_disableInterrupt(adc12, DL_ADC12_INTERRUPT_DMA_DONE);

    DL_ADC12_clearInterruptStatus(adc12, DL_ADC12_INTERRUPT_MEM0_RESULT_LOADED);
    DL_ADC12_enableInterrupt(adc12, DL_ADC12_INTERRUPT_MEM0_RESULT_LOADED);

    DL_ADC12_enableConversions(adc12);
}
