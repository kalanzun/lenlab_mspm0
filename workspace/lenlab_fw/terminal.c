#include "terminal.h"

#include "interpreter.h"

#include "ti_msp_dl_config.h"

#include "arm_acle.h"

struct Terminal terminal = { .rpl = { .label = 'L' }, .rx_flag = false, .tx_flag = false, .rx_stalled = false };

static void terminal_receive(uint32_t address, uint32_t size)
{
    if (terminal.rx_flag) while (true) { __nop(); }
    terminal.rx_flag = true;
    terminal.rx_stalled = false;

    DL_DMA_setDestAddr(DMA, DMA_CH_RX_CHAN_ID, address);
    DL_DMA_setTransferSize(DMA, DMA_CH_RX_CHAN_ID, size);
    DL_DMA_enableChannel(DMA, DMA_CH_RX_CHAN_ID);
}

static void terminal_receivePacket(struct Packet* packet)
{
    terminal_receive((uint32_t)packet, sizeof(*packet));
}

void terminal_receiveCommand(void)
{
    terminal_receivePacket(&terminal.cmd);
}

static void terminal_transmit(uint32_t address, uint32_t size)
{
    if (terminal.tx_flag) while (true) { __nop(); }
    terminal.tx_flag = true;

    DL_DMA_setSrcAddr(DMA, DMA_CH_TX_CHAN_ID, address);
    DL_DMA_setTransferSize(DMA, DMA_CH_TX_CHAN_ID, size);
    DL_DMA_enableChannel(DMA, DMA_CH_TX_CHAN_ID);
}

void terminal_transmitPacket(const struct Packet* packet)
{
    terminal_transmit((uint32_t)packet, packet->length + 8);
}

static void terminal_transmitReply(void)
{
    terminal_transmitPacket(&terminal.rpl);
}

void terminal_sendReply(uint8_t code, uint32_t arg)
{
    terminal.rpl.code = code;
    terminal.rpl.length = 0;
    terminal.rpl.arg = arg;

    terminal_transmitReply();
}

void terminal_init(void)
{
    NVIC_EnableIRQ(TERMINAL_UART_INST_INT_IRQN);

    DL_DMA_setSrcAddr(DMA, DMA_CH_RX_CHAN_ID, (uint32_t)&TERMINAL_UART_INST->RXDATA);
    DL_DMA_setDestAddr(DMA, DMA_CH_TX_CHAN_ID, (uint32_t)&TERMINAL_UART_INST->TXDATA);

    terminal_receiveCommand();
}

void terminal_tick(void)
{
    if (DL_DMA_isChannelEnabled(DMA, DMA_CH_RX_CHAN_ID)) { // RX active
        if (DL_DMA_getTransferSize(DMA, DMA_CH_RX_CHAN_ID) < sizeof(struct Packet)) { // some bytes have arrived
            if (terminal.rx_stalled) { // reset RX
                DL_DMA_disableChannel(DMA, DMA_CH_RX_CHAN_ID);
                terminal.rx_flag = false;
                terminal_receiveCommand();
            } else {
                terminal.rx_stalled = true;
            }
        }
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
        interpreter_handleCommand();
        break;
    default:
        break;
    }
}
