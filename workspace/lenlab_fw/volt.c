#include "volt.h"

#include "terminal.h"

#include "ti_msp_dl_config.h"

struct Volt volt = {
    .adc = {
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

#define POINT_SIZE sizeof(volt.points[0].payload[0])
#define N_POINTS LENGTH(volt.points[0].payload)

#define N_BLOCKS LENGTH(volt.osci.payload[0])
#define N_SAMPLES LENGTH(volt.osci.payload[0][0])

#define WINDOW 3000
#define PRE_BLOCKS 4

void volt_init(void)
{
    NVIC_EnableIRQ(ADC12_CH1_INST_INT_IRQN);
    NVIC_EnableIRQ(ADC12_CH2_INST_INT_IRQN);

    DL_DMA_setSrcAddr(DMA, volt.adc[0].chan_id, (uint32_t)DL_ADC12_getFIFOAddress(volt.adc[0].adc12));
    DL_DMA_setSrcAddr(DMA, volt.adc[1].chan_id, (uint32_t)DL_ADC12_getFIFOAddress(volt.adc[1].adc12));
}

static void volt_initPacket(struct Packet* const self)
{
    self->label = 'L';
    self->code = 'v';
    self->arg = 0;
}

void volt_startLogging(uint32_t interval)
{
    struct Volt* const self = &volt;

    if (interval == 0) { // send points
        // it may be empty
        self->points[self->ping_pong].packet.length = self->point_index * POINT_SIZE;
        terminal_transmitPacket(&self->points[self->ping_pong].packet);

        // ping pong if not empty
        if (self->point_index) {
            self->ping_pong = (self->ping_pong + 1) & 1;
            self->point_index = 0;
        }
    }

    else { // start logging
        /*
            if (DL_Timer_isRunning(VOLT_TIMER_INST)) {
                DL_Timer_stopCounter(VOLT_TIMER_INST);
            }
        */
        volt_initPacket(&self->points[0].packet);
        volt_initPacket(&self->points[1].packet);

        self->ping_pong = 0;
        self->point_index = 0;

        // interval is milliseconds
        // VOLT_TIMER_INST_LOAD_VALUE = (1 s * 50000 Hz) - 1
        DL_Timer_setLoadValue(VOLT_TIMER_INST, interval * 50 - 1);
        DL_Timer_startCounter(VOLT_TIMER_INST);
        terminal_sendReply('v', interval);
    }
}

void volt_stopLogging(void)
{
    DL_Timer_stopCounter(VOLT_TIMER_INST);
    terminal_sendReply('x', ARG_STR("stop"));
}

static void volt_enableDMAChannel(struct ADC* const self)
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

static void volt_startDMAChannel(struct ADC* const self, uint16_t offset)
{
    self->done = false;

    self->block_count = N_BLOCKS + offset;
    self->block_write = N_BLOCKS - offset;

    volt_enableDMAChannel(self);
}

void volt_acquire(uint8_t code, uint16_t interval, uint16_t length)
{
    struct Volt* const self = &volt;

    self->osci.packet.label = 'L';
    self->osci.packet.code = code;
    self->osci.packet.length = sizeof(volt.osci.payload);

    // in units of uint32_t (two samples)
    // one extra double sample for a window including the endpoint
    static const uint16_t end = (N_BLOCKS + PRE_BLOCKS) * N_SAMPLES - 1;
    static const uint16_t mid = end - WINDOW / 2;
    static const uint16_t begin = end - WINDOW;

    uint16_t offset = begin - (mid % (length >> 1)); // double samples

    uint16_t offset_blocks = offset / N_SAMPLES;
    self->osci.packet.arg = interval + ((offset % N_SAMPLES) << 17); // offset in single samples (offset times two)

    volt_startDMAChannel(&self->adc[0], offset_blocks);
    volt_startDMAChannel(&self->adc[1], offset_blocks);

    // interval in 25 ns
    // OSCI_TIMER_INST_LOAD_VALUE = (500 ns * 40 MHz) - 1
    DL_Timer_setLoadValue(MAIN_TIMER_INST, interval - 1);

    DL_Timer_startCounter(MAIN_TIMER_INST);
}

static void volt_handleInterrupt(struct ADC* const self, struct ADC* const other)
{
    uint16_t* point = (uint16_t*)&volt.points[volt.ping_pong].payload[volt.point_index];
    point[self->index] = DL_ADC12_getMemResult(self->adc12, DL_ADC12_MEM_IDX_0);

    self->done = true;

    if (other->done) {
        self->done = false;
        other->done = false;

        volt.point_index = volt.point_index + 1;
        if (volt.point_index >= N_POINTS) {
            // DL_Timer_stopCounter(VOLT_TIMER_INST);
        }
    }
}

static void volt_handleDMAInterrupt(struct ADC* const self, struct ADC* const other)
{
    if (self->block_count == 0) {
        self->done = true;

        if (other->done) {
            DL_Timer_stopCounter(MAIN_TIMER_INST);
            terminal_transmitPacket(&volt.osci.packet);
        }
    } else {
        volt_enableDMAChannel(self);
    }
}

void ADC12_CH1_INST_IRQHandler(void)
{
    static struct ADC* const self = &volt.adc[0];
    static struct ADC* const other = &volt.adc[1];

    switch (DL_ADC12_getPendingInterrupt(self->adc12)) {
    case DL_ADC12_IIDX_MEM0_RESULT_LOADED:
        volt_handleInterrupt(self, other);
        break;
    case DL_ADC12_IIDX_DMA_DONE:
        volt_handleDMAInterrupt(self, other);
        break;
    default:
        break;
    }
}

void ADC12_CH2_INST_IRQHandler(void)
{
    static struct ADC* const self = &volt.adc[1];
    static struct ADC* const other = &volt.adc[0];

    switch (DL_ADC12_getPendingInterrupt(self->adc12)) {
    case DL_ADC12_IIDX_MEM0_RESULT_LOADED:
        volt_handleInterrupt(self, other);
        break;
    case DL_ADC12_IIDX_DMA_DONE:
        volt_handleDMAInterrupt(self, other);
        break;
    default:
        break;
    }
}
