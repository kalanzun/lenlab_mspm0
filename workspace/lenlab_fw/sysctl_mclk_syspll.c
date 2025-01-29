#include "bode.h"
#include "osci.h"
#include "terminal.h"

#include "ti_msp_dl_config.h"

int main(void)
{
    SYSCFG_DL_init();

    osci_init();
    terminal_init();

    while (1) {
        __WFI();
    }
}

void SysTick_Handler(void)
{
    static uint8_t slow_tick = 0;

    bode_tick();

    // 8 * 20 ms = 160 ms
    slow_tick = (slow_tick + 1) & 7;
    if (slow_tick == 0) {
        terminal_tick();
    }
}
