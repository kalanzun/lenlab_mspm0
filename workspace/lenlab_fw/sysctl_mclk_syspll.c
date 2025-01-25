#include "terminal.h"
#include "voltmeter.h"

#include "ti_msp_dl_config.h"

int main(void)
{
    SYSCFG_DL_init();

    terminal_init();
    voltmeter_init();

    while (1) {
        __WFI();
    }
}

void SysTick_Handler(void)
{
    static uint8_t slow_tick = 0;

    // 8 * 20 ms = 160 ms
    slow_tick = (slow_tick + 1) & 7;
    if (slow_tick == 0) {
        terminal_tick();
    }
}
