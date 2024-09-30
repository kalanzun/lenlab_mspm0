#include "ti_msp_dl_config.h"

#include "interpreter.h"
#include "terminal.h"

int main(void)
{
    SYSCFG_DL_init();

    terminal_init();

    while (1) {
        interpreter_main();

        __WFI();
    }
}
