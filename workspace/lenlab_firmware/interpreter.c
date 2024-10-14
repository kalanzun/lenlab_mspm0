#include "interpreter.h"

#include "signal.h"
#include "terminal.h"
#include "version.h"

void version(void)
{
    const char version[] = VERSION;
    uint8_t i = 0;

    terminal.rpl[3] = version[i];
    if (version[i]) i++;
    if (version[i]) i++;

    terminal.rpl[4] = version[i];
    if (version[i]) i++;
    terminal.rpl[5] = version[i];
    if (version[i]) i++;
    terminal.rpl[6] = version[i];
    if (version[i]) i++;
    terminal.rpl[7] = version[i];

    terminal_transmit();
}

void constant(void)
{
    signal_constant(terminal_getArgInt32());
}

void interpreter_main(void)
{
    if (terminal.rx_flag) {
        switch (terminal_getKey()) {
            case '8':
                version();
                break;
            case 'c':
                constant();
                break;
            default:
                break;
        }

        terminal_receive();
    }
}