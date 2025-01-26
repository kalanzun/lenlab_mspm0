#include "osci.h"

#include "ti_msp_dl_config.h"

struct Osci osci = {
    .channel = {
        {
            .packet = {
                .label = 'L',
                .code = 'o',
                .length = sizeof(((struct OsciReply*)0)->payload),
            },
        },
        {
            .packet = {
                .label = 'L',
                .code = 'o',
                .length = sizeof(((struct OsciReply*)0)->payload),
            },
        },
    },
    .ch1_done = false,
    .ch2_done = false,
};

void osci_init(void)
{
    NVIC_EnableIRQ(ADC12_CH1_INST_INT_IRQN);
    NVIC_EnableIRQ(ADC12_CH2_INST_INT_IRQN);
}

void osci_acquire(uint16_t averages)
{
    // sample rate 2 MHz
    // averages: number of averages, valid values are powers of 2: 1, 2, 4, 8, ...

    // avarages 1, sample rate 2 MHz
    // averages 2, sample rate 1 MHz
    // averages 4, sample rate 500 kHz
    // averages 8, sample rate 250 kHz

    const struct Osci* const self = &osci;

    DL_ADC12_configHwAverage(ADC12_CH1_INST, averages, averages);

    DL_DMA_setSrcAddr(DMA, DMA_CH1_CHAN_ID, (uint32_t)DL_ADC12_getFIFOAddress(ADC12_CH1_INST));
    DL_DMA_setDestAddr(DMA, DMA_CH1_CHAN_ID, (uint32_t)self->channel[0].payload);
    /* When FIFO is enabled 2 samples are compacted in a single word */
    DL_DMA_setTransferSize(DMA, DMA_CH1_CHAN_ID, LENGTH(self->channel[0].payload));

    DL_DMA_enableChannel(DMA, DMA_CH1_CHAN_ID);

    DL_ADC12_configHwAverage(ADC12_CH2_INST, averages, averages);

    DL_DMA_setSrcAddr(DMA, DMA_CH2_CHAN_ID, (uint32_t)DL_ADC12_getFIFOAddress(ADC12_CH2_INST));
    DL_DMA_setDestAddr(DMA, DMA_CH2_CHAN_ID, (uint32_t)self->channel[1].payload);
    /* When FIFO is enabled 2 samples are compacted in a single word */
    DL_DMA_setTransferSize(DMA, DMA_CH2_CHAN_ID, LENGTH(self->channel[1].payload));

    DL_DMA_enableChannel(DMA, DMA_CH2_CHAN_ID);

    DL_ADC12_startConversion(ADC12_CH1_INST);
    DL_ADC12_startConversion(ADC12_CH2_INST);

    while (!(osci.ch1_done && osci.ch2_done)) {
        __WFE();
    }
}

void ADC12_CH1_INST_IRQHandler(void)
{
    switch (DL_ADC12_getPendingInterrupt(ADC12_CH1_INST)) {
    case DL_ADC12_IIDX_DMA_DONE:
        osci.ch1_done = true;
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
        break;
    default:
        break;
    }
}
