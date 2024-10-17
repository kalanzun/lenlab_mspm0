#include "terminal.h"

#include "ti_msp_dl_config.h"

struct Terminal terminal;

void terminal_transmit(uint32_t size)
{
    DL_DMA_setSrcAddr(DMA, DMA_CH_TX_CHAN_ID, (uint32_t) terminal.rpl.buffer);
    DL_DMA_setTransferSize(DMA, DMA_CH_TX_CHAN_ID, size);
    DL_DMA_enableChannel(DMA, DMA_CH_TX_CHAN_ID);
}

void terminal_receive(void)
{
    terminal.remember = sizeof(terminal.cmd);

    // remove spurious bytes from the FIFO
    terminal.spurious += DL_UART_Main_drainRXFIFO(TERMINAL_UART_INST, terminal.cmd.buffer, sizeof(terminal.cmd.buffer));

    DL_DMA_setDestAddr(DMA, DMA_CH_RX_CHAN_ID, (uint32_t) terminal.cmd.buffer);
    DL_DMA_setTransferSize(DMA, DMA_CH_RX_CHAN_ID, PACKET_SIZE);
    DL_DMA_enableChannel(DMA, DMA_CH_RX_CHAN_ID);
}

void terminal_init(void)
{
    terminal.flushes = 0;
    terminal.spurious = 0;
    terminal.baudrate_reply = 0;

    NVIC_EnableIRQ(TERMINAL_UART_INST_INT_IRQN);

    DL_DMA_setSrcAddr(DMA, DMA_CH_RX_CHAN_ID, (uint32_t) &TERMINAL_UART_INST->RXDATA);
    terminal_receive();

    DL_DMA_setDestAddr(DMA, DMA_CH_TX_CHAN_ID, (uint32_t) &TERMINAL_UART_INST->TXDATA);
}

bool packet_compare(const struct Packet *a, const struct Packet *b)
{
    for (uint8_t i = 0; i < sizeof(struct Packet); i++)
        if (a->buffer[i] != b->buffer[i])
            return 0;

    return 1;
}

void packet_write(struct Packet *packet, const struct Packet *source)
{
    for (uint8_t i = 0; i < sizeof(struct Packet); i++)
        packet->buffer[i] = source->buffer[i];
}

const struct Packet knock = { .buffer = {'L', 1, 0, 'k', 'n', 'o', 'c', 'k'}, };
const struct Packet bsl_c = { .buffer = {0x80, 1, 0, 0x12, 0x3A, 0x61, 0x44, 0xDE}, };
const struct Packet hello = { .buffer = {'L', 1, 0, 'h', 'e', 'l', 'l', 'o'}, };
const struct Packet get10 = { .buffer = {'L', 1, 0, 'g', 'e', 't', '1', '0'}, };
const struct Packet b4MBd = { .buffer = {'L', 1, 0, 'b', '4', 'M', 'B', 'd'}, };

void terminal_interpreter(void)
{
    if (packet_compare(&terminal.cmd, &knock)) {
        packet_write(&terminal.rpl, &hello);
        terminal_transmit(PACKET_SIZE);
    }
    else if (packet_compare(&terminal.cmd, &bsl_c)) {
        packet_write(&terminal.rpl, &hello);
        terminal_transmit(PACKET_SIZE);
    }
    else if (packet_compare(&terminal.cmd, &get10)) {
        packet_write(&terminal.rpl, &get10);
        terminal_transmit(10);
    }
    else if (packet_compare(&terminal.cmd, &b4MBd)) {
        DL_UART_disable(TERMINAL_UART_INST);
        DL_UART_configBaudRate(TERMINAL_UART_INST, TERMINAL_UART_INST_FREQUENCY, 4000000);

        // delayed reply, the UART needs some time to change
        terminal.baudrate_reply = 2;
    }
}

void terminal_tick(void)
{
    if (DL_DMA_isChannelEnabled(DMA, DMA_CH_RX_CHAN_ID)) { // DMA active
        uint16_t progress = DL_DMA_getTransferSize(DMA, DMA_CH_RX_CHAN_ID);
        if (progress < sizeof(terminal.cmd)) { // some bytes have arrived
            if (progress == terminal.remember) { // but no bytes since last check
                    terminal.flushes += 1; // forget the bytes and restart DMA
                    DL_DMA_disableChannel(DMA, DMA_CH_RX_CHAN_ID);
                    terminal_receive();
            }
            else {
                terminal.remember = progress;
            }
        }
    }

    if (terminal.baudrate_reply) {
        if (terminal.baudrate_reply == 1) {
            DL_UART_enable(TERMINAL_UART_INST);
            packet_write(&terminal.rpl, &b4MBd);
            terminal_transmit(PACKET_SIZE);
        }
        terminal.baudrate_reply -= 1;
    }
}

bool terminal_hasPacketReceived(void)
{
    return !DL_DMA_isChannelEnabled(DMA, DMA_CH_RX_CHAN_ID);
}

void terminal_main(void)
{
    if (terminal_hasPacketReceived()) {
        terminal_interpreter();
        terminal_receive();
    }
}

void TERMINAL_UART_INST_IRQHandler(void)
{
    switch (DL_UART_Main_getPendingInterrupt(TERMINAL_UART_INST)) {
        case DL_UART_MAIN_IIDX_DMA_DONE_TX:
            break;
        case DL_UART_MAIN_IIDX_DMA_DONE_RX:
            break;
        default:
            break;
    }
}
