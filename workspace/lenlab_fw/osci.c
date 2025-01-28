#include "osci.h"

#include "ti_msp_dl_config.h"

struct Osci osci = {
    .packet = {
        .label = 'L',
        .code = 'a',
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

static void osci_configADC(ADC12_Regs* adc12, uint32_t averages)
{
    // sample rate 2 MHz
    // averages: number of averages, valid values are powers of 2: 1, 2, 4, 8, ...

    // avarages 1, sample rate 2 MHz
    // averages 2, sample rate 1 MHz
    // averages 4, sample rate 500 kHz
    // averages 8, sample rate 250 kHz

    DL_ADC12_disableConversions(adc12);

    if (averages == 2)
        DL_ADC12_configHwAverage(adc12, DL_ADC12_HW_AVG_NUM_ACC_2, DL_ADC12_HW_AVG_DEN_DIV_BY_2);
    else if (averages == 4)
        DL_ADC12_configHwAverage(adc12, DL_ADC12_HW_AVG_NUM_ACC_4, DL_ADC12_HW_AVG_DEN_DIV_BY_4);
    else if (averages == 8)
        DL_ADC12_configHwAverage(adc12, DL_ADC12_HW_AVG_NUM_ACC_8, DL_ADC12_HW_AVG_DEN_DIV_BY_8);
    else if (averages == 16)
        DL_ADC12_configHwAverage(adc12, DL_ADC12_HW_AVG_NUM_ACC_16, DL_ADC12_HW_AVG_DEN_DIV_BY_16);
    else
        DL_ADC12_configHwAverage(adc12, DL_ADC12_HW_AVG_NUM_ACC_DISABLED, DL_ADC12_HW_AVG_DEN_DIV_BY_1);

    // DL_ADC12_setSampleTime0(adc12, 12);

    DL_ADC12_enableConversions(adc12);
}

static void osci_configDMAChannel(uint8_t channel, uint32_t src_addr, uint32_t dest_addr, uint16_t size)
{
    DL_DMA_setSrcAddr(DMA, channel, src_addr);
    DL_DMA_setDestAddr(DMA, channel, dest_addr);
    /* When FIFO is enabled 2 samples are compacted in a single word */
    DL_DMA_setTransferSize(DMA, channel, size);

    DL_DMA_enableChannel(DMA, channel);
}

void osci_acquire(uint32_t averages)
{
    struct Osci* const self = &osci;

    self->packet.arg = averages;

    osci_configADC(ADC12_CH1_INST, averages);
    osci_configADC(ADC12_CH2_INST, averages);

    osci_configDMAChannel(DMA_CH1_CHAN_ID, (uint32_t)DL_ADC12_getFIFOAddress(ADC12_CH1_INST), (uint32_t)self->channel[0].payload, LENGTH(self->channel[0].payload));
    osci_configDMAChannel(DMA_CH2_CHAN_ID, (uint32_t)DL_ADC12_getFIFOAddress(ADC12_CH2_INST), (uint32_t)self->channel[1].payload, LENGTH(self->channel[1].payload));

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
