#include "terminal.h"

#include "ti_msp_dl_config.h"

int main(void)
{
    SYSCFG_DL_init();

    NVIC_EnableIRQ(TICK_TIMER_INST_INT_IRQN);

    terminal_init();

    DL_TimerG_startCounter(TICK_TIMER_INST);

    while (1) {
        terminal_main();

        __WFI();
    }
}

void TICK_TIMER_INST_IRQHandler(void)
{
    switch (DL_TimerG_getPendingInterrupt(TICK_TIMER_INST)) {
        case DL_TIMERG_IIDX_ZERO:
            DL_GPIO_togglePins(GPIO_LEDS_PORT, GPIO_LEDS_USER_LED_1_PIN);

            terminal_tick();
            break;
        default:
            break;
    }
}
