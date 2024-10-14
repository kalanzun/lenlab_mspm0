#include "terminal.h"

#include "ti_msp_dl_config.h"

struct Terminal terminal;

uint8_t terminal_getKey(void)
{
    return terminal.cmd[3];
}

int32_t terminal_getArgInt32(void)
{
    return ((int32_t *) (&terminal.cmd[4]))[0];
}

void terminal_transmit(void)
{
    terminal.tx_flag = true;
    DL_DMA_setSrcAddr(DMA, DMA_CH_TERM_TX_CHAN_ID, (uint32_t) terminal.rpl);
    DL_DMA_setTransferSize(DMA, DMA_CH_TERM_TX_CHAN_ID, sizeof(terminal.rpl));
    DL_DMA_enableChannel(DMA, DMA_CH_TERM_TX_CHAN_ID);
}

void terminal_receive(void)
{
    terminal.rx_flag = false;
    terminal.ld_flag = false;
    DL_DMA_setDestAddr(DMA, DMA_CH_TERM_RX_CHAN_ID, (uint32_t) terminal.cmd);
    DL_DMA_setTransferSize(DMA, DMA_CH_TERM_RX_CHAN_ID, sizeof(terminal.cmd));
    DL_DMA_enableChannel(DMA, DMA_CH_TERM_RX_CHAN_ID);
}

void terminal_receive_payload(uint16_t length)
{
    terminal.ld_flag = true;
    DL_DMA_setDestAddr(DMA, DMA_CH_TERM_RX_CHAN_ID, (uint32_t) terminal.pay);
    DL_DMA_setTransferSize(DMA, DMA_CH_TERM_RX_CHAN_ID, length);
    DL_DMA_enableChannel(DMA, DMA_CH_TERM_RX_CHAN_ID);
}

void terminal_init(void)
{
    terminal.rpl[0] = 'L';
    terminal.rpl[1] = 1;
    terminal.rpl[2] = 0;

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
            if (!terminal.ld_flag && terminal.cmd[1] > 1 && terminal.cmd[1] <= sizeof(terminal.pay) && terminal.cmd[2] == 0) {
                terminal_receive_payload(terminal.cmd[1] - 1);  // 7 bytes header
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
