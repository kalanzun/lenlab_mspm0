#include "osci.h"

#include "terminal.h"

#include "ti_msp_dl_config.h"

struct Osci osci = {
    .packet = {
        .label = 'L',
        .length = sizeof(osci.payload),
    },
};

/*
struct ChannelConfig {
    uint8_t index;
    volatile struct Channel *channel;
    volatile struct Channel *other;
    ADC12_Regs *adc12;
    uint8_t dma_channel_id;
};

static const struct ChannelConfig channel_config[2] = {
    {
        .index = 0,
        .channel = &osci.channel[0],
        .other = &osci.channel[1],
        .adc12 = ADC12_CH1_INST,
        .dma_channel_id = DMA_CH1_CHAN_ID,
    },
    {
        .index = 1,
        .channel = &osci.channel[1],
        .other = &osci.channel[0],
        .adc12 = ADC12_CH2_INST,
        .dma_channel_id = DMA_CH2_CHAN_ID,
    },
};
*/

void osci_init(void)
{
    NVIC_EnableIRQ(ADC12_CH1_INST_INT_IRQN);
    NVIC_EnableIRQ(ADC12_CH2_INST_INT_IRQN);

    DL_DMA_setSrcAddr(DMA, DMA_CH1_CHAN_ID, (uint32_t)DL_ADC12_getFIFOAddress(ADC12_CH1_INST));
    DL_DMA_setSrcAddr(DMA, DMA_CH2_CHAN_ID, (uint32_t)DL_ADC12_getFIFOAddress(ADC12_CH2_INST));
}

/*
static inline void channel_continue(const struct ChannelConfig *self)
{
    if (self->channel->block_count) {
        DL_DMA_setDestAddr(DMA, self->dma_channel_id, (uint32_t)osci.payload[self->index][self->channel->block_write]);
        DL_DMA_setTransferSize(DMA, self->dma_channel_id, sizeof(osci.payload[0][0]));
        DL_DMA_enableChannel(DMA, self->dma_channel_id);
        DL_ADC12_enableDMA(self->adc12);

        self->channel->block_count = self->channel->block_count - 1;
        self->channel->block_write = (self->channel->block_write + 1) & 0x7;
    }
    else {
        self->channel->done = true;
        if (self->other->done) {
            DL_Timer_stopCounter(OSCI_TIMER_INST);
            terminal_transmitPacket(&osci.packet);
        }
    }
}
*/

static void osci_startChannel(uint8_t index, ADC12_Regs *adc12, uint8_t chan_id)
{
    volatile struct Channel *const self = &osci.channel[index];

    DL_DMA_setDestAddr(DMA, chan_id, (uint32_t)osci.payload[index][self->block_write]);
    DL_DMA_setTransferSize(DMA, chan_id, LENGTH(osci.payload[0][0]));
    static_assert(LENGTH(osci.payload[0][0]) == 384,
        "DMA size is not 384");
    DL_DMA_enableChannel(DMA, chan_id);
    DL_ADC12_enableDMA(adc12);

    self->block_count = self->block_count - 1;
    self->block_write = (self->block_write + 1) & 0x7;

}

void osci_acquire(uint8_t code, uint32_t interval)
{
    struct Osci* const self = &osci;

    self->packet.code = code;

    self->channel[0].done = false;
    self->channel[0].block_count = 9;
    self->channel[0].block_write = 7;

    osci_startChannel(0, ADC12_CH1_INST, DMA_CH1_CHAN_ID);

    self->channel[1].done = false;
    self->channel[1].block_count = 9;
    self->channel[1].block_write = 7;

    osci_startChannel(1, ADC12_CH2_INST, DMA_CH2_CHAN_ID);

    // interval in 25 ns
    // OSCI_TIMER_INST_LOAD_VALUE = (500 ns * 40 MHz) - 1
    DL_Timer_setLoadValue(MAIN_TIMER_INST, interval - 1);
    
    self->packet.arg = interval;
    
    DL_Timer_startCounter(MAIN_TIMER_INST);
}

void ADC12_CH1_INST_IRQHandler(void)
{
    static volatile struct Channel *const self = &osci.channel[0];

    switch (DL_ADC12_getPendingInterrupt(ADC12_CH1_INST)) {
    case DL_ADC12_IIDX_DMA_DONE:
        if (self->block_count == 0) {
            self->done = true;
            if (osci.channel[1].done) {
                DL_Timer_stopCounter(MAIN_TIMER_INST);
                terminal_transmitPacket(&osci.packet);
            }
        }
        else {
            osci_startChannel(0, ADC12_CH1_INST, DMA_CH1_CHAN_ID);
        }
        break;
    default:
        break;
    }
}

void ADC12_CH2_INST_IRQHandler(void)
{
    static volatile struct Channel *const self = &osci.channel[1];

    switch (DL_ADC12_getPendingInterrupt(ADC12_CH2_INST)) {
    case DL_ADC12_IIDX_DMA_DONE:
        if (self->block_count == 0) {
            self->done = true;
            if (osci.channel[0].done) {
                DL_Timer_stopCounter(MAIN_TIMER_INST);
                terminal_transmitPacket(&osci.packet);
            }
        }
        else {
            osci_startChannel(1, ADC12_CH2_INST, DMA_CH2_CHAN_ID);
        }
        break;
    default:
        break;
    }
}
