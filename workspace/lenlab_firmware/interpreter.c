#include "interpreter.h"

#include "signal.h"
#include "terminal.h"
#include "version.h"

void version(void)
{
    const char version[] = VERSION;
    uint8_t i = 0;

    terminal.rpl.code = version[i];
    if (version[i]) i++;
    if (version[i]) i++;

    terminal.rpl.arg.bytes[0] = version[i];
    if (version[i]) i++;
    terminal.rpl.arg.bytes[1] = version[i];
    if (version[i]) i++;
    terminal.rpl.arg.bytes[2] = version[i];
    if (version[i]) i++;
    terminal.rpl.arg.bytes[3] = version[i];

    terminal_transmit();
}

void constant(void)
{
    signal_constant(terminal.cmd.arg.int32);
}

void interpreter_main(void)
{
    if (terminal.rx_flag) {
        switch (terminal.cmd.code) {
            case '8':
                version();
                break;
            case 'C':
                constant();
                break;
            default:
                break;
        }

        terminal_receive();
    }
}