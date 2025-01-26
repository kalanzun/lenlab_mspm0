#include "terminal.h"

#include "interpreter.h"

#include "ti_msp_dl_config.h"

#include "arm_acle.h"

struct Terminal terminal = { .rpl = { .label = 'L', .length = 0 }, .rx_flag = false, .tx_flag = false, .rx_stalled = false };

static const uint32_t terminal_cmd_packet_size = sizeof(terminal.cmd) + sizeof(terminal.payload);

static void terminal_receive(uint32_t address, uint32_t size)
{
    if (terminal.rx_flag)
        while (true) {
            __nop();
        }
    terminal.rx_flag = true;
    terminal.rx_stalled = false;

    DL_DMA_setDestAddr(DMA, DMA_CH_RX_CHAN_ID, address);
    DL_DMA_setTransferSize(DMA, DMA_CH_RX_CHAN_ID, size);
    DL_DMA_enableChannel(DMA, DMA_CH_RX_CHAN_ID);
}

void terminal_receiveCommand(void)
{
    terminal_receive((uint32_t)&terminal.cmd, terminal_cmd_packet_size);
}

static void terminal_transmit(uint32_t address, uint32_t size)
{
    if (terminal.tx_flag)
        while (true) {
            __nop();
        }
    terminal.tx_flag = true;

    DL_DMA_setSrcAddr(DMA, DMA_CH_TX_CHAN_ID, address);
    DL_DMA_setTransferSize(DMA, DMA_CH_TX_CHAN_ID, size);
    DL_DMA_enableChannel(DMA, DMA_CH_TX_CHAN_ID);
}

void terminal_transmitPacket(const struct Packet* packet)
{
    terminal_transmit((uint32_t)packet, sizeof(*packet) + packet->length);
}

static void terminal_transmitReply(void)
{
    terminal_transmitPacket(&terminal.rpl);
}

void terminal_sendReply(uint8_t code, uint32_t arg)
{
    terminal.rpl.code = code;
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
        if (DL_DMA_getTransferSize(DMA, DMA_CH_RX_CHAN_ID) < terminal_cmd_packet_size) { // some bytes have arrived
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
