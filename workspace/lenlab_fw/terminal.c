#include "terminal.h"

#include "memory.h"

#include "packet.h"
#include "ti_msp_dl_config.h"

static const struct Packet knoc = { .label = lenlab_label, .length = 0, .argument = { 'k', 'n', 'o', 'c' } }; // knock
static const struct Packet mini = { .label = lenlab_label, .length = 0, .argument = { 'm', 'i', 'n', 'i' } }; // memory init
static const struct Packet mget = { .label = lenlab_label, .length = 0, .argument = { 'm', 'g', 'e', 't' } }; // memory get

struct Terminal terminal = { .rx_flag = false, .tx_flag = false, .rx_stalled = false };

static void terminal_receive(uint32_t address, uint32_t size)
{
    while (terminal.rx_flag) { }
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
    while (terminal.tx_flag) { }
    terminal.tx_flag = true;

    DL_DMA_setSrcAddr(DMA, DMA_CH_TX_CHAN_ID, address);
    DL_DMA_setTransferSize(DMA, DMA_CH_TX_CHAN_ID, size);
    DL_DMA_enableChannel(DMA, DMA_CH_TX_CHAN_ID);
}

static void terminal_transmitPacket(const struct Packet* packet)
{
    terminal_transmit((uint32_t)packet, packet->length + 8);
}

void terminal_transmitReply(void)
{
    terminal_transmitPacket(&terminal.rpl);
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

static void terminal_memory_init(void)
{
    uint32_t* restrict payload = (uint32_t*)&memory.payload;

    memory.packet.label = lenlab_label;
    memory.packet.length = sizeof(memory.payload);
    packet_copyArgument(&memory.packet, &mget);

    DL_CRC_setSeed32(CRC, CRC_SEED);
    for (uint32_t i = 0; i < sizeof(memory.payload) / sizeof(*payload); i++) {
        DL_CRC_feedData32(CRC, 0);
        payload[i] = DL_CRC_getResult32(CRC);
    }
}

void terminal_main(void)
{
    if (!terminal.rx_flag) {
        if (terminal.cmd.label == lenlab_label && terminal.cmd.length == 0) {
            switch (terminal.cmd.argument[0]) {
            case 'k':
                if (packet_compareArgument(&terminal.cmd, &knoc)) {
                    terminal_transmitPacket(&knoc);
                }
                break;
            case 'm':
                if (packet_compareArgument(&terminal.cmd, &mini)) {
                    terminal_memory_init();
                    terminal_transmitPacket(&mini);
                } else if (packet_compareArgument(&terminal.cmd, &mget)) {
                    terminal_transmitPacket(&memory.packet);
                }
                break;
            }
        }
        terminal_receiveCommand();
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
