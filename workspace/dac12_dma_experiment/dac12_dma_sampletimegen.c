#include "ti_msp_dl_config.h"

const DL_MathACL_operationConfig gSinOpConfig = {
    .opType      = DL_MATHACL_OP_TYPE_SINCOS,
    .opSign      = DL_MATHACL_OPSIGN_UNSIGNED,
    .iterations  = 10,
    .scaleFactor = 0,
    .qType       = DL_MATHACL_Q_TYPE_Q31};

uint16_t gOutputSignalSine[2048]; // 4 KB

// even numbers
// sample rate 1 MHz
// uint16_t size = 10; // 100 kHz extended range, low time resolution
// uint16_t size = 100; // 10 kHz
uint16_t size = 1000; // 1 kHz
// uint16_t size = 2000; // 500 Hz

// sample rate 500 kHz
// uint16_t size = 1000; // 500 Hz
// uint16_t size = 2000; // 250 Hz

// sample rate 200 kHz
// uint16_t size = 800; // 250 Hz
// uint16_t size = 2000; // 100 Hz

int main(void)
{
    SYSCFG_DL_init();

    uint32_t p = 0x7FFFFFFF / (size >> 1);

    // it does take some time and space to calculate the lookup table
    // then, DMA can feed the DAC without any CPU intervention
    for (uint32_t i = 0; i < size; i++) {
        // DL_MathACL_startSinCosOperation(MATHACL, &gSinOpConfig, ~(i<<20)); für i 0 ... 12bit
        DL_MathACL_startSinCosOperation(MATHACL, &gSinOpConfig, p * i);
        DL_MathACL_waitForOperation(MATHACL);
        gOutputSignalSine[i] = DL_MathACL_getResultTwo(MATHACL) >> 20; // 32 bits down to 12 bits
    }

    /* 0 = 0 degrees */
    /* 0x20000000 = 45 degrees */
    /* 0x40000000 = 90 degrees */
    /* 0x80000000 = 180 degrees */
    // 0x7F...

    /* 0x80000000 = -180 degrees */
    /* 0xC0000000 = -90 degrees */
    /* 0 = 0 degrees */
    // 0xFF...

    DL_DMA_setSrcAddr(DMA, DMA_CH0_CHAN_ID, (uint32_t) gOutputSignalSine);
    DL_DMA_setDestAddr(DMA, DMA_CH0_CHAN_ID, (uint32_t) & (DAC0->DATA0));
    DL_DMA_setTransferSize(DMA, DMA_CH0_CHAN_ID, size);

    DL_DMA_enableChannel(DMA, DMA_CH0_CHAN_ID);

    DL_SYSCTL_enableSleepOnExit();
    while (1) {
        __WFI();
    }
}
