#include "terminal.h"

#include "interpreter.h"

#include "ti_msp_dl_config.h"

struct Terminal terminal = { .rx_flag = false, .tx_flag = false, .rx_stalled = false };

static void terminal_receive(uint32_t address, uint32_t size)
{
    while (terminal.rx_flag) {}
    terminal.rx_flag = true;
    terminal.rx_stalled = false;

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

void terminal_changeBaudrate(enum Baudrate baudrate)
{
    // DMA inactive
    DL_UART_Main_disable(TERMINAL_UART_INST);

    switch (baudrate) {
        case Baudrate_9600:
            DL_UART_Main_setOversampling(TERMINAL_UART_INST, DL_UART_OVERSAMPLING_RATE_16X);
            DL_UART_Main_setBaudRateDivisor(TERMINAL_UART_INST, TERMINAL_UART_IBRD_40_MHZ_9600_BAUD, TERMINAL_UART_FBRD_40_MHZ_9600_BAUD);
            break;
        case Baudrate_4MBd:
            DL_UART_Main_setOversampling(TERMINAL_UART_INST, DL_UART_OVERSAMPLING_RATE_8X);
            DL_UART_Main_setBaudRateDivisor(TERMINAL_UART_INST, 1, 16);
            break;
    }

    DL_UART_Main_enable(TERMINAL_UART_INST);
    // wait for at least 100 ms to send a reply
    // or don't send a reply and wait for the next command
}

void terminal_init(void)
{
    NVIC_EnableIRQ(TERMINAL_UART_INST_INT_IRQN);

    DL_DMA_setSrcAddr(DMA, DMA_CH_RX_CHAN_ID, (uint32_t) &TERMINAL_UART_INST->RXDATA);
    DL_DMA_setDestAddr(DMA, DMA_CH_TX_CHAN_ID, (uint32_t) &TERMINAL_UART_INST->TXDATA);

    terminal_receiveCommand();
}

void terminal_main(void)
{
    if (!terminal.rx_flag) {
        interpreter_main();
    }
}

void terminal_tick(void)
{
    if (DL_DMA_isChannelEnabled(DMA, DMA_CH_RX_CHAN_ID)) { // RX active
        if (DL_DMA_getTransferSize(DMA, DMA_CH_RX_CHAN_ID) < sizeof(Packet)) { // some bytes have arrived
            if (terminal.rx_stalled) { // reset RX
                    DL_DMA_disableChannel(DMA, DMA_CH_RX_CHAN_ID);
                    terminal.rx_flag = false;
                    terminal_receiveCommand();
            }
            else {
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
            break;
        default:
            break;
    }
}
