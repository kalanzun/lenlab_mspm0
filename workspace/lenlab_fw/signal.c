#include "signal.h"

#include "memory.h"

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

void signal_createSinus(uint16_t length, uint16_t amplitude, uint16_t harmonic_multiplier, uint16_t harmonic_amplitude)
{
    struct Packet* const packet = &memory.packet;
    uint16_t* const restrict payload = (uint16_t*)&memory.payload;

    packet->label = 'L';
    packet->code = 'm';
    packet->length = sizeof(*payload) * length;
    packet->arg = ARG_STR("gsin");

    // angle from 0 to 180 degree and then from -180 degree to 0 (not included)
    uint32_t angle = 0;
    uint32_t angle_inc = uq0_div(1 << 31, length >> 1);

    for (uint32_t i = 0; i < length; i++) {
        payload[i] = q31_mul(q31_sin(angle), amplitude);
        angle += angle_inc;
    }

    if (harmonic_amplitude > 0) {
        uint32_t harmonic_angle = 0;
        uint32_t harmonic_angle_inc = angle_inc * harmonic_multiplier;

        for (uint32_t i = 0; i < length; i++) {
            payload[i] += q31_mul(q31_sin(harmonic_angle), harmonic_amplitude);
            harmonic_angle += harmonic_angle_inc;
            if (harmonic_angle < harmonic_angle_inc) {
                // round on overflow
                harmonic_angle = harmonic_angle_inc;
            }
        }
    }
}
