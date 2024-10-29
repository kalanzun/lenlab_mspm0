#include "memory.h"
#include "terminal.h"

#include "ti_msp_dl_config.h"

volatile bool flag = false;

int main(void)
{
    uint16_t blink;

    SYSCFG_DL_init();

    NVIC_EnableIRQ(TICK_TIMER_INST_INT_IRQN);

    DL_TimerG_startCounter(TICK_TIMER_INST);

    terminal_init();

    while (1) {
        if (flag) {
            flag = false;

            blink = (blink + 1) & 15;
            if (blink == 0)
                DL_GPIO_togglePins(GPIO_LEDS_PORT, GPIO_LEDS_USER_LED_1_PIN);

            terminal_main();
        }
        __WFI();
    }
}

void TICK_TIMER_INST_IRQHandler(void)
{
    switch (DL_TimerG_getPendingInterrupt(TICK_TIMER_INST)) {
    case DL_TIMERG_IIDX_ZERO:
        flag = true;

        terminal_tick();
        break;
    default:
        break;
    }
}
