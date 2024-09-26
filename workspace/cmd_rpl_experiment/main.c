#include "ti_msp_dl_config.h"

struct Message {
    uint8_t ack;
    uint8_t code;
    uint16_t length;
    uint32_t arg;
};

struct Terminal {
    bool rx_flag;
    bool payload_mode;
    struct Message cmd;
    struct Message rpl;
    uint8_t payload[4096];

};

volatile struct Terminal terminal;


void echo(void)
{
    terminal.rpl.ack = 'L';
    terminal.rpl.code = 'E';
    terminal.rpl.length = terminal.cmd.length;
    terminal.rpl.arg = terminal.cmd.arg;

    DL_DMA_setSrcAddr(DMA, DMA_CH0_CHAN_ID, (uint32_t) &terminal.rpl);
    DL_DMA_setTransferSize(DMA, DMA_CH0_CHAN_ID, sizeof(terminal.rpl) + terminal.rpl.length);
    DL_DMA_enableChannel(DMA, DMA_CH0_CHAN_ID);
}

int main(void)
{
    SYSCFG_DL_init();

    /* TX */
    DL_DMA_setDestAddr(DMA, DMA_CH0_CHAN_ID, (uint32_t) &UART_0_INST->TXDATA);

    /* RX */
    /* Configure DMA source, destination and size */
    DL_DMA_setSrcAddr(DMA, DMA_CH1_CHAN_ID, (uint32_t) &UART_0_INST->RXDATA);

    terminal.payload_mode = false;
    DL_DMA_setDestAddr(DMA, DMA_CH1_CHAN_ID, (uint32_t) &terminal.cmd);
    DL_DMA_setTransferSize(DMA, DMA_CH1_CHAN_ID, sizeof(terminal.cmd));
    
    terminal.rx_flag = false;
    DL_DMA_enableChannel(DMA, DMA_CH1_CHAN_ID);

    NVIC_EnableIRQ(UART_0_INST_INT_IRQN);

    while (1) {
        if (terminal.rx_flag) {
            if (terminal.payload_mode) {
                switch (terminal.cmd.code) {
                    case 'E':
                        echo();
                        break;
                    default:
                        break;
                }
                terminal.payload_mode = false;
                DL_DMA_setDestAddr(DMA, DMA_CH1_CHAN_ID, (uint32_t) &terminal.cmd);
                DL_DMA_setTransferSize(DMA, DMA_CH1_CHAN_ID, sizeof(terminal.cmd));
            }
            else {
                terminal.payload_mode = true;
                DL_DMA_setDestAddr(DMA, DMA_CH1_CHAN_ID, (uint32_t) &terminal.payload);
                DL_DMA_setTransferSize(DMA, DMA_CH1_CHAN_ID, terminal.cmd.length);
            }

            terminal.rx_flag = false;
            DL_DMA_enableChannel(DMA, DMA_CH1_CHAN_ID);
        }

        __WFE();
    }
}

void UART_0_INST_IRQHandler(void)
{
    switch (DL_UART_Main_getPendingInterrupt(UART_0_INST)) {
        case DL_UART_MAIN_IIDX_EOT_DONE:
            break;
        case DL_UART_MAIN_IIDX_DMA_DONE_TX:
            break;
        case DL_UART_MAIN_IIDX_DMA_DONE_RX:
            terminal.rx_flag = true;
            break;
        default:
            break;
    }
}
