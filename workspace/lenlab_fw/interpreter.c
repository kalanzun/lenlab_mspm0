#include "interpreter.h"

#include "memory.h"
#include "terminal.h"
#include "version.h"
#include "voltmeter.h"

#include "ti_msp_dl_config.h"

static void interpreter_init28K(void)
{
    struct Packet* const packet = &memory.packet;
    uint32_t* const restrict payload = (uint32_t*)&memory.payload;

    packet->label = 'L';
    packet->code = 'm';
    packet->length = sizeof(memory.payload);
    packet->arg = ARG_STR("g28K");

    DL_CRC_setSeed32(CRC, CRC_SEED);
    for (uint32_t i = 0; i < sizeof(memory.payload) / sizeof(*payload); i++) {
        DL_CRC_feedData32(CRC, 0);
        payload[i] = DL_CRC_getResult32(CRC);
    }

    terminal_sendReply('m', ARG_STR("i28K"));
}

static void interpreter_getVersion(void)
{
    const char version[] = VERSION;
    uint8_t i = 0;

    uint32_t arg = 0;

    // handle any version string length
    if (version[i])
        i++;
    if (version[i])
        i++;

    arg += version[i];
    if (version[i])
        i++;
    arg += version[i] << 8;
    if (version[i])
        i++;
    arg += version[i] << 16;
    if (version[i])
        i++;
    arg += version[i] << 24;

    terminal_sendReply(VERSION[0], arg);
}

void interpreter_handleCommand(void)
{
    const struct Packet* const cmd = &terminal.cmd;

    if (cmd->label == 'L' && cmd->length == 0) {
        DL_GPIO_togglePins(GPIO_LEDS_B_PORT, GPIO_LEDS_B_LED_GREEN_PIN);
        switch (cmd->code) {
        case 'k': // knock
            if (cmd->arg == ARG_STR("nock")) {
                terminal_sendReply('k', ARG_STR("nock"));
            }
            break;
        case VERSION[0]: // 8
            if (cmd->arg == ARG_STR("ver?")) { // version
                interpreter_getVersion();
            }
            break;
        case 'm': // memory
            if (cmd->arg == ARG_STR("i28K")) { // init 28K
                interpreter_init28K();
            } else if (cmd->arg == ARG_STR("g28K")) { // get 28K
                terminal_transmitPacket(&memory.packet);
            }
            break;
        case 'v': // voltmeter
            if (cmd->arg == ARG_STR("next")) { // next
                voltmeter_next();
            } else if (cmd->arg == ARG_STR("stop")) { // stop
                voltmeter_stop();
            } else { // assume start and interval argument
                voltmeter_start(cmd->arg);
            }
            break;
        }
    }
    terminal_receiveCommand();
}
