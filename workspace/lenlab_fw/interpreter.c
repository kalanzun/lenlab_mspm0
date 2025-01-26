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
        case 's': // signal generator
            if (cmd->arg == ARG_STR("star")) { // start
                signal_start(0);
                terminal_sendReply('s', ARG_STR("star"));
            } else if (cmd->arg == ARG_STR("stop")) { // stop
                signal_stop();
                terminal_sendReply('s', ARG_STR("stop"));
            } else if (cmd->arg == ARG_STR("sinu")) { // create sinus
                signal_createSinus(2000, 1024);
                terminal_sendReply('s', ARG_STR("sinu"));
            } else if (cmd->arg == ARG_STR("harm")) { // add harmonic
                signal_addHarmonic(20, 1024);
                terminal_sendReply('s', ARG_STR("harm"));
            } else if (cmd->arg == ARG_STR("get?")) { // get data
                terminal_transmitPacket(&signal.reply.packet);
            }
            break;
        case 'o': // oscilloscope
            if (cmd->arg == ARG_STR("run!")) { // run
                osci_run();
                terminal_sendReply('o', ARG_STR("run!"));
            } else if (cmd->arg == ARG_STR("ch1?")) { // get channel 1
                terminal_transmitPacket(&osci.channel[0].packet);
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
