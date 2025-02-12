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

void osci_init(void)
{
    NVIC_EnableIRQ(ADC12_CH1_INST_INT_IRQN);
    NVIC_EnableIRQ(ADC12_CH2_INST_INT_IRQN);

    DL_DMA_setSrcAddr(DMA, osci.channel[0].chan_id, (uint32_t)DL_ADC12_getFIFOAddress(osci.channel[0].adc12));
    DL_DMA_setSrcAddr(DMA, osci.channel[1].chan_id, (uint32_t)DL_ADC12_getFIFOAddress(osci.channel[1].adc12));
}

static void osci_initChannel(struct Channel* const self, uint16_t block_offset)
{
    self->done = false;

    self->block_count = LENGTH(osci.payload[0]) + block_offset;
    self->block_write = LENGTH(osci.payload[0]) - block_offset;
}

static void osci_enableChannel(struct Channel* const self)
{
    DL_DMA_setDestAddr(DMA, self->chan_id, (uint32_t)osci.payload[self->index][self->block_write]);
    DL_DMA_setTransferSize(DMA, self->chan_id, LENGTH(osci.payload[0][0]));
    DL_DMA_enableChannel(DMA, self->chan_id);
    DL_ADC12_enableDMA(self->adc12);

    self->block_count = self->block_count - 1;
    static_assert(LENGTH(osci.payload[0]) == 16, "block count is not 16");
    self->block_write = (self->block_write + 1) & 0xF;
}

void osci_acquire(uint8_t code, uint16_t interval, uint16_t length)
{
    struct Osci* const self = &osci;

    self->packet.code = code;

    static_assert(LENGTH(osci.payload[0]) == 16, "block count is not 16");
    static_assert(LENGTH(osci.payload[0][0]) == 216, "sample count is not 216");
    // end = 5184 = (16 + 8) blocks * 216 double samples
    // mid = 3684 = end - window / 2; (3000 / 2)
    // begin = 2184 = end - window
    
    uint16_t offset = 2184 - (3684 % (length >> 1)); // double samples
    // min case: offset = 1266

    uint16_t block_offset = offset / 216;
    self->packet.arg = interval + ((offset % 216) << 17); // offset in samples (times 2)

    osci_initChannel(&self->channel[0], block_offset);
    osci_enableChannel(&self->channel[0]);

    osci_initChannel(&self->channel[1], block_offset);
    osci_enableChannel(&self->channel[1]);

    // interval in 25 ns
    // OSCI_TIMER_INST_LOAD_VALUE = (500 ns * 40 MHz) - 1
    DL_Timer_setLoadValue(MAIN_TIMER_INST, interval - 1);


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

    switch (DL_ADC12_getPendingInterrupt(self->adc12)) {
    case DL_ADC12_IIDX_DMA_DONE:
        if (self->block_count == 0) {
            osci_finishChannel(self, &osci.channel[1]);
        } else {
            osci_enableChannel(self);
        }
        break;
    default:
        break;
    }
}

void ADC12_CH2_INST_IRQHandler(void)
{
    static struct Channel* const self = &osci.channel[1];

    switch (DL_ADC12_getPendingInterrupt(self->adc12)) {
    case DL_ADC12_IIDX_DMA_DONE:
        if (self->block_count == 0) {
            osci_finishChannel(self, &osci.channel[0]);
        } else {
            osci_enableChannel(self);
        }
        break;
    default:
        break;
    }
}
