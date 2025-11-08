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

static_assert(sizeof(volt.wave.payload) == 27 * 1024, "27 KB");

#define POINT_SIZE sizeof(volt.points[0].payload[0])
#define N_POINTS LENGTH(volt.points[0].payload)

#define WAVEFORM_SIZE sizeof(volt.wave.payload)
#define N_BLOCKS LENGTH(volt.wave.payload[0])
#define N_SAMPLES LENGTH(volt.wave.payload[0][0])

#define WINDOW 3000
#define PRE_BLOCKS 4

static void volt_initADC(struct ADC* const self)
{
    // Just setting those to DL_ADC12_HW_AVG_NUM_ACC_DISABLED for osci mode does not work. The timing is broken, then.
    DL_ADC12_configHwAverage(self->adc12, DL_ADC12_HW_AVG_NUM_ACC_16, DL_ADC12_HW_AVG_DEN_DIV_BY_16);

    DL_DMA_setSrcAddr(DMA, self->chan_id, (uint32_t)DL_ADC12_getFIFOAddress(self->adc12));
}

void volt_init(void)
{
    struct Volt* const self = &volt;

    NVIC_EnableIRQ(ADC12_CH1_INST_INT_IRQN);
    NVIC_EnableIRQ(ADC12_CH2_INST_INT_IRQN);

    volt_initADC(&self->adc[0]);
    volt_initADC(&self->adc[1]);
}

static void volt_configConversionMemory0(struct ADC* const self, bool sample_time_source, bool averaging)
{
    // requires previous DL_ADC12_disableConversions
    volatile uint32_t* const memctl = &self->adc12->ULLMEM.MEMCTL[DL_ADC12_MEM_IDX_0];

    if (sample_time_source) {
        *memctl |= ADC12_MEMCTL_STIME_MASK;
    } else {
        *memctl &= ~ADC12_MEMCTL_STIME_MASK;
    }

    if (averaging) {
        *memctl |= ADC12_MEMCTL_AVGEN_MASK;
    } else {
        *memctl &= ~ADC12_MEMCTL_AVGEN_MASK;
    }
}

static void volt_setLoggerMode(struct ADC* const self)
{
    DL_ADC12_disableConversions(self->adc12);

    volt_configConversionMemory0(self, 1, 1);

    DL_ADC12_disableFIFO(self->adc12);

    DL_ADC12_disableInterrupt(self->adc12, (DL_ADC12_INTERRUPT_DMA_DONE | DL_ADC12_INTERRUPT_MEM0_RESULT_LOADED));
    DL_ADC12_clearInterruptStatus(self->adc12, (DL_ADC12_INTERRUPT_DMA_DONE | DL_ADC12_INTERRUPT_MEM0_RESULT_LOADED));
    DL_ADC12_enableInterrupt(self->adc12, (DL_ADC12_INTERRUPT_MEM0_RESULT_LOADED));

    DL_ADC12_enableConversions(self->adc12);
}

static void volt_setOsciMode(struct ADC* const self)
{
    DL_ADC12_disableConversions(self->adc12);

    volt_configConversionMemory0(self, 0, 0);

    DL_ADC12_enableFIFO(self->adc12);

    DL_ADC12_disableInterrupt(self->adc12, (DL_ADC12_INTERRUPT_DMA_DONE | DL_ADC12_INTERRUPT_MEM0_RESULT_LOADED));
    DL_ADC12_clearInterruptStatus(self->adc12, (DL_ADC12_INTERRUPT_DMA_DONE | DL_ADC12_INTERRUPT_MEM0_RESULT_LOADED));
    DL_ADC12_enableInterrupt(self->adc12, (DL_ADC12_INTERRUPT_DMA_DONE));

    DL_ADC12_enableConversions(self->adc12);
}

void volt_startLogging(uint32_t interval)
{
    struct Volt* const self = &volt;

    DL_Timer_stopCounter(MAIN_TIMER_INST);

    volt_setLoggerMode(&self->adc[0]);
    volt_setLoggerMode(&self->adc[1]);

    packet_write(&self->points[0].packet, 'x', 0, 1);
    packet_write(&self->points[1].packet, 'x', 0, 1);

    self->ping_pong = 0;
    self->point_index = 0;
    self->point_reset = 0;

    // interval in 25 ns
    DL_Timer_setLoadValue(MAIN_TIMER_INST, interval - 1);
    DL_Timer_startCounter(MAIN_TIMER_INST);

    terminal_sendReply('v', interval);
}

void volt_getPoints(uint32_t polling)
{
    struct Volt* const self = &volt;

    if (polling == 0) { // stop logging
        self->points[self->ping_pong].packet.arg = 0;
        DL_Timer_stopCounter(MAIN_TIMER_INST);
    }

    // send points
    // it may be empty
    self->points[self->ping_pong].packet.length = self->point_index * POINT_SIZE;
    terminal_transmitPacket(&self->points[self->ping_pong].packet);

    // ping pong if not empty
    if (self->point_index) {
        self->ping_pong = (self->ping_pong + 1) & 1;
        self->point_index = self->point_reset;
    }
}

void volt_createLoggingExampleData(uint32_t interval)
{
    struct Volt* const self = &volt;

    DL_Timer_stopCounter(MAIN_TIMER_INST);

    packet_write(&self->points[0].packet, 'v', 0, 0);
    packet_write(&self->points[1].packet, 'v', 0, 0);

    for (uint16_t i = 0; i < N_POINTS; i++) {
        self->points[0].payload[i] = (i << 2) | ((4096 - (i << 2)) << 16);
        self->points[1].payload[i] = (4096 - (i << 2)) | ((i << 2) << 16);
    }

    self->ping_pong = 0;
    self->point_index = N_POINTS;
    self->point_reset = N_POINTS;

    terminal_sendReply('u', interval);
}

static void volt_enableDMAChannel(struct ADC* const self)
{
    DL_DMA_setDestAddr(DMA, self->chan_id, (uint32_t)volt.wave.payload[self->index][volt.block_write]);
    static_assert(N_SAMPLES % 6 == 0, "DMA and FIFO require divisibility by 12 samples or 6 uint32_t");
    DL_DMA_setTransferSize(DMA, self->chan_id, N_SAMPLES);
    DL_DMA_enableChannel(DMA, self->chan_id);
    DL_ADC12_enableDMA(self->adc12);
}

static void volt_enableDMA(void)
{
    struct Volt* const self = &volt;

    volt_enableDMAChannel(&self->adc[0]);
    volt_enableDMAChannel(&self->adc[1]);

    self->block_count = self->block_count - 1;
    static_assert(IS_POWER_OF_TWO(N_BLOCKS), "efficient ring buffer implementation");
    self->block_write = (self->block_write + 1) & (N_BLOCKS - 1);
}

void volt_acquireWaveform(uint8_t code, uint16_t interval, uint16_t length)
{
    struct Volt* const self = &volt;

    DL_Timer_stopCounter(MAIN_TIMER_INST);

    volt_setOsciMode(&self->adc[0]);
    volt_setOsciMode(&self->adc[1]);

    // in units of uint32_t (two samples)
    // one extra double sample for a window including the endpoint
    static const uint16_t end = (N_BLOCKS + PRE_BLOCKS) * N_SAMPLES - 1;
    static const uint16_t mid = end - WINDOW / 2;
    static const uint16_t begin = end - WINDOW;

    uint16_t offset = begin - (mid % (length >> 1)); // double samples

    uint16_t offset_blocks = offset / N_SAMPLES;
    packet_write(&self->wave.packet, code, WAVEFORM_SIZE, interval + ((offset % N_SAMPLES) << 17)); // offset in single samples (offset times two)

    self->block_count = N_BLOCKS + offset_blocks;
    self->block_write = N_BLOCKS - offset_blocks;

    volt_enableDMA();

    // interval in 25 ns
    // OSCI_TIMER_INST_LOAD_VALUE = (500 ns * 40 MHz) - 1
    DL_Timer_setLoadValue(MAIN_TIMER_INST, interval - 1);
    DL_Timer_startCounter(MAIN_TIMER_INST);
}

static inline uint32_t volt_getResult(struct ADC* const self)
{
    return DL_ADC12_getMemResult(self->adc12, DL_ADC12_MEM_IDX_0);
}

static void volt_handlePoint(void)
{
    struct Volt* const self = &volt;

    self->points[self->ping_pong].payload[self->point_index] = (volt_getResult(&self->adc[0])
        + (volt_getResult(&self->adc[1]) << 16));

    self->point_index = self->point_index + 1;
    if (self->point_index >= N_POINTS) {
        DL_Timer_stopCounter(MAIN_TIMER_INST);
    }
}

static void volt_handleWaveform(void)
{
    struct Volt* const self = &volt;

    if (self->block_count == 0) {
        DL_Timer_stopCounter(MAIN_TIMER_INST);
        terminal_transmitPacket(&self->wave.packet);
    } else {
        volt_enableDMA();
    }
}

static void volt_IRQHandler(struct ADC* const self, struct ADC* const other)
{
    // the handler must read the pending interrupt value
    const DL_ADC12_IIDX iidx = DL_ADC12_getPendingInterrupt(self->adc12);

    if (other->done) {
        other->done = false;

        switch (iidx) {
        case DL_ADC12_IIDX_MEM0_RESULT_LOADED:
            volt_handlePoint();
            break;
        case DL_ADC12_IIDX_DMA_DONE:
            volt_handleWaveform();
            break;
        default:
            break;
        }
    } else {
        self->done = true;
    }
}

void ADC12_CH1_INST_IRQHandler(void)
{
    volt_IRQHandler(&volt.adc[0], &volt.adc[1]);
}

void ADC12_CH2_INST_IRQHandler(void)
{
    volt_IRQHandler(&volt.adc[1], &volt.adc[0]);
}
