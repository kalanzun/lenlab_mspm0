#include "terminal.h"

#include "ti_msp_dl_config.h"

volatile uint8_t blink = 0;

int main(void)
{
    SYSCFG_DL_init();

    terminal_init();

    while (1) {
        if (blink == 0)
            DL_GPIO_togglePins(GPIO_LEDS_PORT, GPIO_LEDS_USER_LED_1_PIN);

        __WFI();
    }
}

void SysTick_Handler(void)
{
    blink = (blink + 1) & 31;

    terminal_tick();
}
