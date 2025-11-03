#include "volt.h"

#include "terminal.h"

#include "ti_msp_dl_config.h"

struct Volt volt = {
    .osci.packet = {
        .label = 'L',
        .length = sizeof(volt.osci.payload),
    },
    .channel = {
        {
            .index = 0,
            .adc12 = ADC12_CH1_INST,
            .chan_id = DMA_CH1_CHAN_ID,
        },
        {
            .index = 1,
            .adc12 = ADC12_CH2_INST,
            .chan_id = DMA_CH2_CHAN_ID,
        },
    },
};

static_assert(sizeof(volt.osci.payload) == 27 * 1024, "27 KB");

#define N_BLOCKS LENGTH(volt.osci.payload[0])
#define N_SAMPLES LENGTH(volt.osci.payload[0][0])

#define WINDOW 3000
#define PRE_BLOCKS 4

void osci_init(void)
{
    NVIC_EnableIRQ(ADC12_CH1_INST_INT_IRQN);
    NVIC_EnableIRQ(ADC12_CH2_INST_INT_IRQN);

    DL_DMA_setSrcAddr(DMA, volt.channel[0].chan_id, (uint32_t)DL_ADC12_getFIFOAddress(volt.channel[0].adc12));
    DL_DMA_setSrcAddr(DMA, volt.channel[1].chan_id, (uint32_t)DL_ADC12_getFIFOAddress(volt.channel[1].adc12));
}

static void osci_initChannel(struct Channel* const self, uint16_t offset)
{
    self->done = false;

    self->block_count = N_BLOCKS + offset;
    self->block_write = N_BLOCKS - offset;
}

static void osci_enableChannel(struct Channel* const self)
{
    DL_DMA_setDestAddr(DMA, self->chan_id, (uint32_t)volt.osci.payload[self->index][self->block_write]);
    static_assert(N_SAMPLES % 6 == 0, "DMA and FIFO require divisibility by 12 samples or 6 uint32_t");
    DL_DMA_setTransferSize(DMA, self->chan_id, N_SAMPLES);
    DL_DMA_enableChannel(DMA, self->chan_id);
    DL_ADC12_enableDMA(self->adc12);

    self->block_count = self->block_count - 1;
    static_assert(IS_POWER_OF_TWO(N_BLOCKS), "efficient ring buffer implementation");
    self->block_write = (self->block_write + 1) & (N_BLOCKS - 1);
}

void osci_acquire(uint8_t code, uint16_t interval, uint16_t length)
{
    struct Volt* const self = &volt;

    self->osci.packet.code = code;

    // in units of uint32_t (two samples)
    // one extra double sample for a window including the endpoint
    static const uint16_t end = (N_BLOCKS + PRE_BLOCKS) * N_SAMPLES - 1;
    static const uint16_t mid = end - WINDOW / 2;
    static const uint16_t begin = end - WINDOW;

    uint16_t offset = begin - (mid % (length >> 1)); // double samples

    uint16_t offset_blocks = offset / N_SAMPLES;
    self->osci.packet.arg = interval + ((offset % N_SAMPLES) << 17); // offset in single samples (offset times two)

    osci_initChannel(&self->channel[0], offset_blocks);
    osci_enableChannel(&self->channel[0]);

    osci_initChannel(&self->channel[1], offset_blocks);
    osci_enableChannel(&self->channel[1]);

    // interval in 25 ns
    // OSCI_TIMER_INST_LOAD_VALUE = (500 ns * 40 MHz) - 1
    DL_Timer_setLoadValue(MAIN_TIMER_INST, interval - 1);

    DL_Timer_startCounter(MAIN_TIMER_INST);
}

static void osci_handleDMAInterrupt(struct Channel* const self, struct Channel* const other)
{
    if (self->block_count == 0) {
        self->done = true;

        if (other->done) {
            DL_Timer_stopCounter(MAIN_TIMER_INST);
            terminal_transmitPacket(&volt.osci.packet);
        }
    } else {
        osci_enableChannel(self);
    }
}

void ADC12_CH1_INST_IRQHandler(void)
{
    static struct Channel* const self = &volt.channel[0];
    static struct Channel* const other = &volt.channel[1];

    switch (DL_ADC12_getPendingInterrupt(self->adc12)) {
    case DL_ADC12_IIDX_DMA_DONE:
        osci_handleDMAInterrupt(self, other);
        break;
    default:
        break;
    }
}

void ADC12_CH2_INST_IRQHandler(void)
{
    static struct Channel* const self = &volt.channel[1];
    static struct Channel* const other = &volt.channel[0];

    switch (DL_ADC12_getPendingInterrupt(self->adc12)) {
    case DL_ADC12_IIDX_DMA_DONE:
        osci_handleDMAInterrupt(self, other);
        break;
    default:
        break;
    }
}
