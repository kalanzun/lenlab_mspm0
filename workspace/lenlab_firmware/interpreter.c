#include "interpreter.h"

#include "terminal.h"
#include "version.h"

void version(void)
{
    const char version[] = VERSION;
    uint8_t i = 0;

    terminal.rpl.code = version[i];
    if (version[i]) i++;
    if (version[i]) i++;

    terminal.rpl.arg0 = version[i];
    if (version[i]) i++;
    terminal.rpl.arg1 = version[i];
    if (version[i]) i++;
    terminal.rpl.arg2 = version[i];
    if (version[i]) i++;
    terminal.rpl.arg3 = version[i];

    terminal_transmit();
}

void interpreter_main(void)
{
    if (terminal.rx_flag) {
        switch (terminal.cmd.code) {
            case '8':
                version();
                break;
            default:
                break;
        }

        terminal_receive();
    }
}