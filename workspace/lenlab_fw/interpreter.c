#include "interpreter.h"

#include "osci.h"
#include "signal.h"
#include "terminal.h"
#include "version.h"
#include "voltmeter.h"

#include "ti_msp_dl_config.h"

static void interpreter_getVersion(void)
{
    const char version[] = VERSION;
    uint8_t i = 0;

    uint32_t arg = 0;

    // handle any version string length
    if (version[i]) // 8
        i++;
    if (version[i]) // .
        i++;

    for (; version[i] != 0 && version[i] != '.' && i < 6; i++) {
        arg += version[i] << ((i - 2) * 8);
    }

    terminal_sendReply(VERSION[0], arg);
}

void interpreter_handleCommand(void)
{
    const struct Terminal* const self = &terminal;
    const struct Packet* const cmd = &terminal.cmd;

    if (cmd->label == 'L' && cmd->length == sizeof(self->payload)) {
        DL_GPIO_togglePins(GPIO_LEDS_B_PORT, GPIO_LEDS_B_LED_GREEN_PIN);
        switch (cmd->code) {
        case 'k': // knock
            if (cmd->arg == ARG_STR("nock")) {
                terminal_sendReply('k', ARG_STR("nock"));
            }
            break;

        case VERSION[0]: // 8
            if (cmd->arg == ARG_STR("ver?")) { // get version
                interpreter_getVersion();
            }
            break;

        case 's': // signal generator
            if (cmd->arg == ARG_STR("sin!")) { // sinus
                signal_sinus(self->payload[0], self->payload[1], self->payload[2], self->payload[3]);
                terminal_sendReply('s', ARG_STR("sin!"));
            } else if (cmd->arg == ARG_STR("stop")) { // stop
                signal_stop();
                terminal_sendReply('s', ARG_STR("stop"));
            } else if (cmd->arg == ARG_STR("dat?")) { // get data
                terminal_transmitPacket(&signal.packet);
            }
            break;

        case 'o': // oscilloscope
            if (cmd->arg == ARG_STR("acq!")) { // acquire
                osci_acquire(self->payload[0]);
                terminal_sendReply('o', ARG_STR("acq!"));
            } else if (cmd->arg == ARG_STR("ch1?")) { // get channel 1
                terminal_transmitPacket(&osci.channel[0].packet);
            } else if (cmd->arg == ARG_STR("ch2?")) { // get channel 2
                terminal_transmitPacket(&osci.channel[1].packet);
            }
            break;

            /*
            case 'v': // voltmeter
                if (cmd->arg == ARG_STR("next")) { // next
                    voltmeter_next();
                } else if (cmd->arg == ARG_STR("stop")) { // stop
                    voltmeter_stop();
                } else { // assume start and interval argument
                    voltmeter_start(cmd->arg);
                }
                break;
            */
        }
    }
    terminal_receiveCommand();
}
