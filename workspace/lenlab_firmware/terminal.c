#include "terminal.h"

#include "interpreter.h"

#include "ti_msp_dl_config.h"

struct Terminal terminal = { .rx_flag = false, .tx_flag = false };

static void terminal_receive(uint32_t address, uint32_t size)
{
    while (terminal.rx_flag) {}
    terminal.rx_flag = true;

    DL_DMA_setDestAddr(DMA, DMA_CH_RX_CHAN_ID, address);
    DL_DMA_setTransferSize(DMA, DMA_CH_RX_CHAN_ID, size);
    DL_DMA_enableChannel(DMA, DMA_CH_RX_CHAN_ID);
}

static void terminal_receivePacket(Packet *packet)
{
    terminal_receive((uint32_t) packet, sizeof(*packet));
}

void terminal_receiveCommand(void)
{
    terminal_receivePacket(&terminal.cmd);
}

static void terminal_transmit(uint32_t address, uint32_t size)
{
    while (terminal.tx_flag) {}
    terminal.tx_flag = true;

    DL_DMA_setSrcAddr(DMA, DMA_CH_TX_CHAN_ID, address);
    DL_DMA_setTransferSize(DMA, DMA_CH_TX_CHAN_ID, size);
    DL_DMA_enableChannel(DMA, DMA_CH_TX_CHAN_ID);
}

void terminal_transmitPacket(const Packet *packet)
{
    terminal_transmit((uint32_t) packet, sizeof(*packet));
}

void terminal_transmitReply(void)
{
    terminal_transmitPacket(&terminal.rpl);
}

void terminal_init(void)
{
    NVIC_EnableIRQ(TERMINAL_UART_INST_INT_IRQN);

    DL_DMA_setSrcAddr(DMA, DMA_CH_RX_CHAN_ID, (uint32_t) &TERMINAL_UART_INST->RXDATA);
    terminal_receiveCommand();

    DL_DMA_setDestAddr(DMA, DMA_CH_TX_CHAN_ID, (uint32_t) &TERMINAL_UART_INST->TXDATA);
}

void terminal_main(void)
{
    if (!terminal.rx_flag) {
        interpreter_main();
    }
}

void TERMINAL_UART_INST_IRQHandler(void)
{
    switch (DL_UART_Main_getPendingInterrupt(TERMINAL_UART_INST)) {
        case DL_UART_MAIN_IIDX_DMA_DONE_TX:
            terminal.tx_flag = false;
            break;
        case DL_UART_MAIN_IIDX_DMA_DONE_RX:
            terminal.rx_flag = false;
            break;
        case DL_UART_MAIN_IIDX_RX_TIMEOUT_ERROR:
            break;
        default:
            break;
    }
}
