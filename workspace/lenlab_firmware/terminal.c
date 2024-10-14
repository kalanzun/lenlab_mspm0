#include "terminal.h"

#include "ti_msp_dl_config.h"

struct Terminal terminal;

void terminal_transmit(void)
{
    terminal.tx_flag = true;
    DL_DMA_setSrcAddr(DMA, DMA_CH_TERM_TX_CHAN_ID, (uint32_t) &terminal.rpl);
    DL_DMA_setTransferSize(DMA, DMA_CH_TERM_TX_CHAN_ID, sizeof(terminal.rpl));
    DL_DMA_enableChannel(DMA, DMA_CH_TERM_TX_CHAN_ID);
}

void terminal_receive(void)
{
    terminal.rx_flag = false;
    terminal.ld_flag = false;
    DL_DMA_setDestAddr(DMA, DMA_CH_TERM_RX_CHAN_ID, (uint32_t) &terminal.cmd);
    DL_DMA_setTransferSize(DMA, DMA_CH_TERM_RX_CHAN_ID, sizeof(terminal.cmd));
    DL_DMA_enableChannel(DMA, DMA_CH_TERM_RX_CHAN_ID);
}

void terminal_receive_payload(uint16_t length)
{
    terminal.ld_flag = true;
    DL_DMA_setDestAddr(DMA, DMA_CH_TERM_RX_CHAN_ID, (uint32_t) &terminal.payload);
    DL_DMA_setTransferSize(DMA, DMA_CH_TERM_RX_CHAN_ID, length);
    DL_DMA_enableChannel(DMA, DMA_CH_TERM_RX_CHAN_ID);
}

void terminal_init(void)
{
    terminal.rpl.ack = 'L';
    terminal.rpl.code = 0;
    terminal.rpl.length = 0;
    terminal.rpl.arg.uint32 = 0;

    NVIC_EnableIRQ(TERMINAL_UART_INST_INT_IRQN);

    DL_DMA_setSrcAddr(DMA, DMA_CH_TERM_RX_CHAN_ID, (uint32_t) &TERMINAL_UART_INST->RXDATA);
    terminal_receive();

    DL_DMA_setDestAddr(DMA, DMA_CH_TERM_TX_CHAN_ID, (uint32_t) &TERMINAL_UART_INST->TXDATA);
    terminal.tx_flag = false;
}

void TERMINAL_UART_INST_IRQHandler(void)
{
    switch (DL_UART_Main_getPendingInterrupt(TERMINAL_UART_INST)) {
        case DL_UART_MAIN_IIDX_DMA_DONE_RX:
            if (!terminal.ld_flag && terminal.cmd.length > 0 && terminal.cmd.length <= sizeof(terminal.payload)) {
                terminal_receive_payload(terminal.cmd.length);
            }
            else {
                terminal.rx_flag = true;
                terminal.ld_flag = false;
            }
            break;
        case DL_UART_MAIN_IIDX_DMA_DONE_TX:
            terminal.tx_flag = false;
            break;
        default:
            break;
    }
}
