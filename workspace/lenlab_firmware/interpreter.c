#include "interpreter.h"

#include "packet.h"
#include "terminal.h"

static const Packet bsl_c = { .buffer = { 0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE } };
static const Packet knock = { .buffer = { 'L', 'k', 0, 0, 'n', 'o', 'c', 'k' } };

void interpreter_main(void)
{
    static const Packet * const cmd = &terminal.cmd;
    static const Packet * const rpl = &terminal.rpl;

    if (cmd->label == 'L' && cmd->length == 0) {
        switch (cmd->key) {
            case 'k':
                if (packet_comparePayload(cmd, &knock)) {
                    terminal_transmitPacket(&knock);
                }
        }
    }

    else if (packet_comparePacket(cmd, &bsl_c)) {
        terminal_transmitPacket(&knock);
    }

    terminal_receiveCommand();
}
