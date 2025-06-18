#include "interpreter.h"

#include "osci.h"
#include "signal.h"
#include "terminal.h"
#include "version.h"
#include "volt.h"

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
            terminal_sendReply('k', ARG_STR("nock"));
            break;

        case VERSION[0]: // 8
            interpreter_getVersion();
            break;

        case 's': // sinus
            signal_sinus(self->payload[0], self->payload[1], self->payload[2], self->payload[3]);
            terminal_transmitPacket(&signal.packet);
            break;

        case 'a': // acquire
            signal_sinus(self->payload[0], self->payload[1], self->payload[2], self->payload[3]);
            osci_acquire('a', cmd->arg, self->payload[0]);
            break;

        case 'b': // bode
            signal_sinus(self->payload[0], self->payload[1], 0, 0);
            osci_acquire('b', cmd->arg, self->payload[0]);
            break;

        case 'v': // volt
            if (cmd->arg == ARG_STR("next")) { // next
                volt_next();
            } else if (cmd->arg == ARG_STR("stop")) { // stop
                volt_stop();
            } else if (cmd->arg == ARG_STR("strt")) { // start
                volt_start(self->payload[0]);
            }
            break;
        }
    }
}
