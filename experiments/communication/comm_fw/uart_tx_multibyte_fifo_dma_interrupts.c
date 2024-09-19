#include "ti_msp_dl_config.h"

const uint8_t gPacket[4096];

volatile bool gCheckUART, gDMADone, gEOT;

#define LENGTH(_array) (sizeof (_array) / sizeof *(_array))

int main(void)
{
    SYSCFG_DL_init();

    /* Configure DMA source, destination and size */
    DL_DMA_setSrcAddr(DMA, DMA_CH1_CHAN_ID, (uint32_t)(&UART_0_INST->RXDATA));
    DL_DMA_setDestAddr(DMA, DMA_CH1_CHAN_ID, (uint32_t) gPacket);
    DL_DMA_setTransferSize(DMA, DMA_CH1_CHAN_ID, LENGTH(gPacket));
    DL_DMA_enableChannel(DMA, DMA_CH1_CHAN_ID);

    /* Confirm DMA channel is enabled */
    while (false == DL_DMA_isChannelEnabled(DMA, DMA_CH1_CHAN_ID)) {
        __BKPT(0);
    }
    NVIC_EnableIRQ(UART_0_INST_INT_IRQN);
    gCheckUART = false;
    DL_SYSCTL_disableSleepOnExit();
    /* Wait in SLEEP mode until DMA interrupt is triggered */
    while (false == gCheckUART) {
        __WFE();
    }

    // DL_SYSCTL_enableSleepOnExit();
    // DL_SYSCTL_disableSleepOnExit();

    // echo back 256 times
    for (uint16_t i = 0; i < 256; i++) {
        /* Configure DMA source, destination and size */
        DL_DMA_setSrcAddr(DMA, DMA_CH0_CHAN_ID, (uint32_t) gPacket);
        DL_DMA_setDestAddr(DMA, DMA_CH0_CHAN_ID, (uint32_t)(&UART_0_INST->TXDATA));
        DL_DMA_setTransferSize(DMA, DMA_CH0_CHAN_ID, LENGTH(gPacket));

        gEOT = false;
        gDMADone   = false;

        /*
        * The UART DMA TX interrupt is set indicating the UART is ready to
        * transmit data, so enabling the DMA will start the transfer
        */
        DL_DMA_enableChannel(DMA, DMA_CH0_CHAN_ID);

        /* Wait in SLEEP mode until DMA interrupt is triggered */
        while (false == gDMADone) {
            __WFE();
        }

    }

    /* Wait until all bytes have been transmitted and the TX FIFO is empty */
    while (false == gEOT) {
        __WFE();
    }

    DL_SYSCTL_enableSleepOnExit();
    while (1) {
        /* LED will turn ON to indicate example has completed without error */
        DL_GPIO_clearPins(GPIO_LEDS_PORT,
            (GPIO_LEDS_USER_LED_1_PIN | GPIO_LEDS_USER_TEST_PIN));
        __WFI();
    }
}

void UART_0_INST_IRQHandler(void)
{
    switch (DL_UART_Main_getPendingInterrupt(UART_0_INST)) {
        case DL_UART_MAIN_IIDX_EOT_DONE:
            gEOT = true;
            break;
        case DL_UART_MAIN_IIDX_DMA_DONE_TX:
            gDMADone = true;
            break;
        case DL_UART_MAIN_IIDX_DMA_DONE_RX:
            gCheckUART = true;
            break;
        default:
            break;
    }
}
