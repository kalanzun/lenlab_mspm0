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
    uint32_t amplitude = DL_MathACL_getResultTwo(MATHACL);
    // it might calculate a value just one bit smaller than -1 at -90 degrees
    return angle & (1ul << 31) && amplitude == (1ul << 31) - 1 ? (1ul << 31) : amplitude;
}

static int32_t q31_mul(int32_t a, int32_t b)
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
        .code = 's',
        .length = sizeof(signal.payload),
    },
};

void signal_init(void)
{
    DL_DAC12_performSelfCalibrationBlocking(DAC0);
    DL_MathACL_enableSaturation(MATHACL);
}

static uint32_t uq0_angle_inc(uint32_t length)
{
    // length: even number of samples
    return uq0_div(1ul << 31, length >> 1);
}

static uint32_t q31_sinus(uint32_t angle, uint32_t amplitude)
{
    return q31_mul(q31_sin(angle), amplitude);
}

static void signal_createSinus(uint16_t length, uint16_t amplitude)
{
    struct Signal* const self = &signal;

    // angle from 0 to 180 degree and then from -180 degree to 0 (0 not included)
    uint32_t angle = 0;
    uint32_t angle_inc = uq0_angle_inc(length);

    for (uint16_t i = 0; i < length; i++) {
        self->payload[i] = q31_sinus(angle, amplitude);
        angle += angle_inc;
    }
}

static void signal_addHarmonic(uint16_t length, uint16_t multiplier, uint16_t amplitude)
{
    struct Signal* const self = &signal;

    // angle from 0 to 180 degree and then from -180 degree to 0 (not included)
    uint32_t angle = 0;
    uint32_t angle_inc = uq0_angle_inc(length) * multiplier;

    for (uint32_t i = 0; i < length; i++) {
        self->payload[i] += q31_sinus(angle, amplitude);
        angle += angle_inc;
    }
}

void signal_sinus(uint16_t length, uint16_t amplitude, uint16_t multiplier, uint16_t harmonic)
{
    struct Signal* const self = &signal;

    self->packet.arg = length;

    // disable channel for safe reconfiguration
    DL_DMA_disableChannel(DMA, DMA_CH0_CHAN_ID);

    signal_createSinus(length, amplitude);

    if (multiplier > 1 && harmonic > 0)
        signal_addHarmonic(length, multiplier, harmonic);

    DL_DMA_setSrcAddr(DMA, DMA_CH0_CHAN_ID, (uint32_t)self->payload);
    DL_DMA_setDestAddr(DMA, DMA_CH0_CHAN_ID, (uint32_t) & (DAC0->DATA0));
    DL_DMA_setTransferSize(DMA, DMA_CH0_CHAN_ID, length);

    DL_DMA_enableChannel(DMA, DMA_CH0_CHAN_ID);
}
