#include "signal.h"
#include "terminal.h"
#include "volt.h"


#include "ti_msp_dl_config.h"

int main(void)
{
    SYSCFG_DL_init();

    volt_init();
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
