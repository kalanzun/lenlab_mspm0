#include "memory.h"
#include "terminal.h"

#include "ti_msp_dl_config.h"

static bool tick = false;

int main(void)
{
    uint8_t blink = 0;

    SYSCFG_DL_init();

    NVIC_EnableIRQ(TICK_TIMER_INST_INT_IRQN);

    DL_TimerG_startCounter(TICK_TIMER_INST);

    terminal_init();

    memory_init();

    while (1) {
        if (tick) {
            tick = false;

            terminal_main();

            blink = (blink + 1) & 15;
            if (blink == 0)
                DL_GPIO_togglePins(GPIO_LEDS_PORT, GPIO_LEDS_USER_LED_1_PIN);
        }

        __WFI();
    }
}

void TICK_TIMER_INST_IRQHandler(void)
{
    switch (DL_TimerG_getPendingInterrupt(TICK_TIMER_INST)) {
    case DL_TIMERG_IIDX_ZERO:
        tick = true;
        terminal_tick();
        break;
    default:
        break;
    }
}
