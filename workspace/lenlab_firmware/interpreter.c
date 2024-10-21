#include "interpreter.h"

#include "memory.h"
#include "terminal.h"

static const Packet bsl_c = { .buffer = { 0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE } };
static const Packet knock = { .buffer = { 'L', 'k', 0, 0, 'n', 'o', 'c', 'k' } };
static const Packet b4MBd = { .buffer = { 'L', 'b', 0, 0, '4', 'M', 'B', 'd' } };
static const Packet b9600 = { .buffer = { 'L', 'b', 0, 0, '9', '6', '0', '0' } };
static const Packet m30KB = { .buffer = { 'L', 'm', 0, 0, '3', '0', 'K', 'B' } };

void interpreter_main(void)
{
    static const Packet* const cmd = &terminal.cmd;
    // static const Packet * const rpl = &terminal.rpl;

    if (cmd->label == 'L' && cmd->length == 0) {
        switch (cmd->key) {
        case 'k':
            if (packet_comparePayload(cmd, &knock)) {
                terminal_transmitPacket(&knock);
            }
            break;
        case 'b':
            if (packet_comparePayload(cmd, &b4MBd)) {
                terminal_changeBaudrate(Baudrate_4MBd);
            } else if (packet_comparePayload(cmd, &b9600)) {
                terminal_changeBaudrate(Baudrate_9600);
            }
            break;
        case 'm':
            if (packet_comparePayload(cmd, &m30KB)) {
                terminal_transmitPacket(&memory.packet);
            }
            break;
        }
    } else if (packet_comparePacket(cmd, &bsl_c)) {
        terminal_transmitPacket(&knock);
    }

    terminal_receiveCommand();
}
