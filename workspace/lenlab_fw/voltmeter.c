#include "voltmeter.h"

#include "packet.h"
#include "terminal.h"

#include "ti_msp_dl_config.h"

struct Voltmeter voltmeter = {
    .flag = NO_FLAG,
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
    .ping_pong = false,
    .point_index = 0,
    .interval = 0,
    .time = 0,
};

void voltmeter_start(uint32_t interval)
{
    struct Voltmeter* const self = &voltmeter;

    if (DL_Timer_isRunning(VOLT_TIMER_INST)) {
        DL_Timer_stopCounter(VOLT_TIMER_INST);
    }

    self->ping_pong = 0;
    self->point_index = 0;
    self->interval = interval;
    self->time = 0;

    // VOLT_TIMER_INST_LOAD_VALUE = (1 s * 50000 Hz) - 1
    DL_Timer_setLoadValue(VOLT_TIMER_INST, interval * 50 - 1);
    DL_Timer_startCounter(VOLT_TIMER_INST);
    terminal_sendReply('v', ARG_STR("strt"));
}

void voltmeter_next(void)
{
    struct Voltmeter* const self = &voltmeter;

    struct VoltmeterReply* const reply = &self->reply[self->ping_pong];

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

void voltmeter_stop(void)
{
    DL_Timer_stopCounter(VOLT_TIMER_INST);
    terminal_sendReply('v', ARG_STR("stop"));
}

void voltmeter_init(void)
{
    NVIC_EnableIRQ(ADC12_0_INST_INT_IRQN);
    NVIC_EnableIRQ(ADC12_1_INST_INT_IRQN);
}

static void voltmeter_handleADCResult(void)
{
    struct Voltmeter* const self = &voltmeter;

    struct VoltmeterReply* const reply = &self->reply[self->ping_pong];
    struct VoltmeterPoint* const point = &reply->points[self->point_index];

    // DL_GPIO_togglePins(GPIO_LEDS_PORT, GPIO_LEDS_USER_LED_1_PIN);

    self->point_index = self->point_index + 1;
    if (self->point_index == LENGTH(reply->points)) {
        DL_Timer_stopCounter(VOLT_TIMER_INST);
        return;
    }

    point->time = self->time;
    self->time += self->interval;

    point->ch1 = DL_ADC12_getMemResult(ADC12_0_INST, DL_ADC12_MEM_IDX_0);
    point->ch2 = DL_ADC12_getMemResult(ADC12_1_INST, DL_ADC12_MEM_IDX_0);

    self->flag = NO_FLAG;
}

void ADC12_0_INST_IRQHandler(void)
{
    switch (DL_ADC12_getPendingInterrupt(ADC12_0_INST)) {
    case DL_ADC12_IIDX_MEM0_RESULT_LOADED:
        voltmeter.flag |= FLAG_ADC0;
        if (voltmeter.flag == FLAG_BOTH)
            voltmeter_handleADCResult();
        break;
    default:
        break;
    }
}

void ADC12_1_INST_IRQHandler(void)
{
    switch (DL_ADC12_getPendingInterrupt(ADC12_1_INST)) {
    case DL_ADC12_IIDX_MEM0_RESULT_LOADED:
        voltmeter.flag |= FLAG_ADC1;
        if (voltmeter.flag == FLAG_BOTH)
            voltmeter_handleADCResult();
        break;
    default:
        break;
    }
}
