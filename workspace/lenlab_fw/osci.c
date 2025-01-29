#include "osci.h"

#include "terminal.h"

#include "ti_msp_dl_config.h"

struct Osci osci = {
    .packet = {
        .label = 'L',
        .length = sizeof(osci.channel),
    },
    .ch1_done = false,
    .ch2_done = false,
};

void osci_init(void)
{
    NVIC_EnableIRQ(ADC12_CH1_INST_INT_IRQN);
    NVIC_EnableIRQ(ADC12_CH2_INST_INT_IRQN);
}

void osci_acquire(uint8_t code, uint32_t interval)
{
    struct Osci* const self = &osci;

    self->packet.code = code;

    self->ch1_done = false;
    self->ch2_done = false;

    DL_DMA_setSrcAddr(DMA, DMA_CH1_CHAN_ID, (uint32_t)DL_ADC12_getFIFOAddress(ADC12_CH1_INST));
    DL_DMA_setDestAddr(DMA, DMA_CH1_CHAN_ID, (uint32_t)self->channel[0].payload);
    /* When FIFO is enabled 2 samples are compacted in a single word */
    DL_DMA_setTransferSize(DMA, DMA_CH1_CHAN_ID, LENGTH(self->channel[0].payload));

    DL_DMA_setSrcAddr(DMA, DMA_CH2_CHAN_ID, (uint32_t)DL_ADC12_getFIFOAddress(ADC12_CH2_INST));
    DL_DMA_setDestAddr(DMA, DMA_CH2_CHAN_ID, (uint32_t)self->channel[1].payload);
    /* When FIFO is enabled 2 samples are compacted in a single word */
    DL_DMA_setTransferSize(DMA, DMA_CH2_CHAN_ID, LENGTH(self->channel[1].payload));

    DL_DMA_enableChannel(DMA, DMA_CH1_CHAN_ID);
    DL_DMA_enableChannel(DMA, DMA_CH2_CHAN_ID);

    // interval in 100 ns
    // OSCI_TIMER_INST_LOAD_VALUE = (500 ns * 10 MHz) - 1
    DL_Timer_setLoadValue(OSCI_TIMER_INST, interval - 1);
    self->packet.arg = interval;
    DL_Timer_startCounter(OSCI_TIMER_INST);
}

void osci_handleResult(void)
{
    struct Osci* const self = &osci;

    if (self->ch1_done && self->ch2_done) {
        DL_Timer_stopCounter(OSCI_TIMER_INST);
        terminal_transmitPacket(&self->packet);
    }
}

void ADC12_CH1_INST_IRQHandler(void)
{
    switch (DL_ADC12_getPendingInterrupt(ADC12_CH1_INST)) {
    case DL_ADC12_IIDX_DMA_DONE:
        osci.ch1_done = true;
        osci_handleResult();
        break;
    default:
        break;
    }
}

void ADC12_CH2_INST_IRQHandler(void)
{
    switch (DL_ADC12_getPendingInterrupt(ADC12_CH2_INST)) {
    case DL_ADC12_IIDX_DMA_DONE:
        osci.ch2_done = true;
        osci_handleResult();
        break;
    default:
        break;
    }
}
