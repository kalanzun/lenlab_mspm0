#include "signal.h"
#include "terminal.h"

#include "ti_msp_dl_config.h"

static uint32_t q31_sin(uint32_t angle)
{
    static const DL_MathACL_operationConfig sinus_config = {
        .opType = DL_MATHACL_OP_TYPE_SINCOS,
        .opSign = DL_MATHACL_OPSIGN_SIGNED,
        .iterations = 10,
        .scaleFactor = 0,
        .qType = DL_MATHACL_Q_TYPE_Q31
    };

    DL_MathACL_startSinCosOperation(MATHACL, &sinus_config, angle);
    DL_MathACL_waitForOperation(MATHACL);
    return DL_MathACL_getResultTwo(MATHACL);
}

static uint32_t q31_mul(uint32_t a, uint32_t b)
{
    static const DL_MathACL_operationConfig mpy_config = {
        .opType = DL_MATHACL_OP_TYPE_MPY_32,
        .opSign = DL_MATHACL_OPSIGN_SIGNED,
        .iterations = 1,
        .scaleFactor = 0,
        .qType = DL_MATHACL_Q_TYPE_Q31
    };

    DL_MathACL_startMpyOperation(MATHACL, &mpy_config, a, b);
    DL_MathACL_waitForOperation(MATHACL);
    return DL_MathACL_getResultOne(MATHACL);
}

static uint32_t uq0_div(uint32_t dividend, uint32_t divisor)
{
    static const DL_MathACL_operationConfig div_config = {
        .opType = DL_MATHACL_OP_TYPE_DIV,
        .opSign = DL_MATHACL_OPSIGN_UNSIGNED,
        .iterations = 0,
        .scaleFactor = 1,
        .qType = DL_MATHACL_Q_TYPE_Q0
    };

    DL_MathACL_startDivOperation(MATHACL, &div_config, dividend, divisor);
    DL_MathACL_waitForOperation(MATHACL);
    return DL_MathACL_getResultOne(MATHACL);
}

struct Signal signal = {
    .packet = {
        .label = 'L',
        .code = 'g',
        .length = sizeof(signal.payload),
    },
};

static void signal_createSinus(uint16_t length, uint16_t amplitude)
{
    struct Signal* const self = &signal;

    self->length = length;
    self->packet.arg = length;

    // angle from 0 to 180 degree and then from -180 degree to 0 (not included)
    uint32_t angle = 0;
    uint32_t angle_inc = uq0_div(1 << 31, length >> 1);

    // my board produces a calculation error for length = 1024 or length = 512
    // it's a single wrong value near i = 800

    for (uint32_t i = 0; i < length; i++) {
        self->payload[i] = q31_mul(q31_sin(angle), amplitude);
        angle += angle_inc;
    }
}

static void signal_addHarmonic(uint16_t multiplier, uint16_t amplitude)
{
    struct Signal* const self = &signal;

    uint16_t length = self->length;

    // angle from 0 to 180 degree and then from -180 degree to 0 (not included)
    uint32_t angle = 0;
    uint32_t angle_inc = uq0_div(1 << 31, length >> 1) * multiplier;

    for (uint32_t i = 0; i < length; i++) {
        self->payload[i] += q31_mul(q31_sin(angle), amplitude);
        angle += angle_inc;
        if (angle < angle_inc) {
            // round on overflow
            angle = angle_inc;
        }
    }
}

void signal_sinus(uint32_t sample_rate, uint16_t length, uint16_t amplitude, uint16_t multiplier, uint16_t harmonic)
{
    struct Signal* const self = &signal;

    DL_DAC12_disableSampleTimeGenerator(DAC0);

    // disable channel for safe reconfiguration
    DL_DMA_disableChannel(DMA, DMA_CH0_CHAN_ID);

    if (sample_rate == 200)
        DL_DAC12_setSampleRate(DAC0, DL_DAC12_SAMPLES_PER_SECOND_200K);
    else if (sample_rate == 500)
        DL_DAC12_setSampleRate(DAC0, DL_DAC12_SAMPLES_PER_SECOND_500K);
    else if (sample_rate == 1000)
        DL_DAC12_setSampleRate(DAC0, DL_DAC12_SAMPLES_PER_SECOND_1M);
    else
        return;

    if (length < 100 || length > 2000)
        return;

    if (amplitude == 0 || amplitude >= 2048 || amplitude & 1u)
        return;

    signal_createSinus(length, amplitude);

    if (multiplier > 0 && harmonic > 0)
        signal_addHarmonic(multiplier, harmonic);

    DL_DMA_setSrcAddr(DMA, DMA_CH0_CHAN_ID, (uint32_t)self->payload);
    DL_DMA_setDestAddr(DMA, DMA_CH0_CHAN_ID, (uint32_t) & (DAC0->DATA0));
    DL_DMA_setTransferSize(DMA, DMA_CH0_CHAN_ID, length);

    DL_DMA_enableChannel(DMA, DMA_CH0_CHAN_ID);

    DL_DAC12_enableSampleTimeGenerator(DAC0);
}
