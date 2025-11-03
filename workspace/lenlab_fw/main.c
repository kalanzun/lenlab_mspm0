#include "volt.h"
#include "signal.h"
#include "terminal.h"

#include "ti_msp_dl_config.h"

int main(void)
{
    SYSCFG_DL_init();

    osci_init();
    signal_init();
    terminal_init();

    while (1) {
        __WFI();
    }
}

void SysTick_Handler(void)
{
    // 200 ms
    terminal_tick();
}
