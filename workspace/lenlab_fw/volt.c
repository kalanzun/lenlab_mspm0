#include "volt.h"

#include "adc.h"
#include "packet.h"
#include "terminal.h"

#include "ti_msp_dl_config.h"

struct Volt volt = {
    .reply = {
        {
            .packet = {
                .label = 'L',
                .code = 'v',
                .length = 0,
                .arg = ARG_STR(" red"),
            },
        },
        {
            .packet = {
                .label = 'L',
                .code = 'v',
                .length = 0,
                .arg = ARG_STR(" blu"),
            },
        },
    },
};

void volt_start(uint32_t interval)
{
    struct Volt* const self = &volt;

    if (DL_Timer_isRunning(VOLT_TIMER_INST)) {
        DL_Timer_stopCounter(VOLT_TIMER_INST);
    }

    // promise to send red first
    self->ping_pong = 0;
    self->point_index = 0;
    self->interval = interval;
    self->time = 0;

    adc_reconfigureVolt(&adc[0]);
    adc_reconfigureVolt(&adc[1]);

    adc_restart(&adc[0]);
    adc_restart(&adc[1]);

    // VOLT_TIMER_INST_LOAD_VALUE = (1 s * 50000 Hz) - 1
    DL_Timer_setLoadValue(VOLT_TIMER_INST, interval * 50 - 1);
    DL_Timer_startCounter(VOLT_TIMER_INST);
    terminal_sendReply('v', ARG_STR("strt"));
}

void volt_next(void)
{
    struct Volt* const self = &volt;

    struct VoltReply* const reply = &self->reply[self->ping_pong];

    // UART interrupt and ADC interrupt run at the same priority
    // so _next and _main cannot interrupt each other

    if (!DL_Timer_isRunning(VOLT_TIMER_INST)) {
        terminal_sendReply('v', ARG_STR("err!"));
        return;
    }

    // it may be empty
    reply->packet.length = self->point_index * sizeof(*reply->points);
    terminal_transmitPacket(&reply->packet);

    // ping pong if not empty
    if (self->point_index) {
        self->ping_pong = !self->ping_pong;
        self->point_index = 0;
    }
}

void volt_stop(void)
{
    DL_Timer_stopCounter(VOLT_TIMER_INST);
    terminal_sendReply('v', ARG_STR("stop"));
}

void volt_callback(void)
{
    struct Volt* const self = &volt;

    struct VoltReply* const reply = &self->reply[self->ping_pong];
    struct VoltPoint* const point = &reply->points[self->point_index];

    // next ADC measurement might already be underway
    if (!DL_Timer_isRunning(VOLT_TIMER_INST)) {
        return;
    }

    DL_GPIO_togglePins(GPIO_LEDS_B_PORT, GPIO_LEDS_B_LED_BLUE_PIN);

    self->point_index = self->point_index + 1;
    if (self->point_index >= LENGTH(reply->points)) {
        DL_Timer_stopCounter(VOLT_TIMER_INST);
        return;
    }

    point->time = self->time;
    self->time += self->interval;

    point->ch[0] = adc_getResult(&adc[0]);
    point->ch[1] = adc_getResult(&adc[1]);

    adc_restart(&adc[0]);
    adc_restart(&adc[1]);
}
