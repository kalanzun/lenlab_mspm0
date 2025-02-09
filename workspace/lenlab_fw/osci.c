#include "osci.h"

#include "terminal.h"

#include "ti_msp_dl_config.h"

struct Osci osci = {
    .packet = {
        .label = 'L',
        .length = sizeof(osci.payload),
    },
    .channel = {
        {
            .index = 0,
        },
        {
            .index = 1,
        },
    },
};

void osci_init(void)
{
    NVIC_EnableIRQ(ADC12_CH1_INST_INT_IRQN);
    NVIC_EnableIRQ(ADC12_CH2_INST_INT_IRQN);

    DL_DMA_setSrcAddr(DMA, DMA_CH1_CHAN_ID, (uint32_t)DL_ADC12_getFIFOAddress(ADC12_CH1_INST));
    DL_DMA_setSrcAddr(DMA, DMA_CH2_CHAN_ID, (uint32_t)DL_ADC12_getFIFOAddress(ADC12_CH2_INST));
}

static void osci_initChannel(struct Channel* const self)
{
    self->done = false;
    // two extra blocks
    self->block_count = LENGTH(osci.payload[0]) + 2;
    self->block_write = LENGTH(osci.payload[0]) - 2;
}

static void osci_enableChannel(struct Channel* const self, ADC12_Regs* adc12, uint8_t chan_id)
{
    DL_DMA_setDestAddr(DMA, chan_id, (uint32_t)osci.payload[self->index][self->block_write]);
    DL_DMA_setTransferSize(DMA, chan_id, LENGTH(osci.payload[0][0]));
    DL_DMA_enableChannel(DMA, chan_id);
    DL_ADC12_enableDMA(adc12);

    self->block_count = self->block_count - 1;
    self->block_write = (self->block_write + 1) & 0x7;
}

void osci_acquire(uint8_t code, uint32_t interval)
{
    struct Osci* const self = &osci;

    self->packet.code = code;

    osci_initChannel(&self->channel[0]);
    osci_enableChannel(&self->channel[0], ADC12_CH1_INST, DMA_CH1_CHAN_ID);

    osci_initChannel(&self->channel[1]);
    osci_enableChannel(&self->channel[1], ADC12_CH2_INST, DMA_CH2_CHAN_ID);

    // interval in 25 ns
    // OSCI_TIMER_INST_LOAD_VALUE = (500 ns * 40 MHz) - 1
    DL_Timer_setLoadValue(MAIN_TIMER_INST, interval - 1);

    self->packet.arg = interval;

    DL_Timer_startCounter(MAIN_TIMER_INST);
}

static void osci_finishChannel(struct Channel* const self, struct Channel* const other)
{
    self->done = true;
    if (other->done) {
        DL_Timer_stopCounter(MAIN_TIMER_INST);
        terminal_transmitPacket(&osci.packet);
    }
}

void ADC12_CH1_INST_IRQHandler(void)
{
    static struct Channel* const self = &osci.channel[0];

    switch (DL_ADC12_getPendingInterrupt(ADC12_CH1_INST)) {
    case DL_ADC12_IIDX_DMA_DONE:
        if (self->block_count == 0) {
            osci_finishChannel(self, &osci.channel[1]);
        } else {
            osci_enableChannel(self, ADC12_CH1_INST, DMA_CH1_CHAN_ID);
        }
        break;
    default:
        break;
    }
}

void ADC12_CH2_INST_IRQHandler(void)
{
    static struct Channel* const self = &osci.channel[1];

    switch (DL_ADC12_getPendingInterrupt(ADC12_CH2_INST)) {
    case DL_ADC12_IIDX_DMA_DONE:
        if (self->block_count == 0) {
            osci_finishChannel(self, &osci.channel[0]);
        } else {
            osci_enableChannel(self, ADC12_CH2_INST, DMA_CH2_CHAN_ID);
        }
        break;
    default:
        break;
    }
}
