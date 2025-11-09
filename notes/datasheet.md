# Datasheet

## DAC

1 channel

12 bit resolution

up to 2000 samples

sample rates: 200 kHz, 500 kHz, or 1 MHz (common timer with ADC)

frequency range: 100 Hz to 10 kHz

peak-to-peak voltage: 3.3 V

max amplitude: 1.65 V

virtual zero at mid-level between GND and 3V3

second signal frequency multiplier: 0 to 20

The second signal is another sine signal added to the output signal with a fixed frequency multiplier. Both sine signals have the same amplitude, which is half the amplitude setting in the Lenlab software. The sum of both is at most equal to the amplitude setting.

## ADC

2 channels

12 bit resolution

## Oscilloscope and Bode-Plot

up to 6000 samples (each channel)

sample rates: 200 kHz, 500 kHz, or 1 MHz (common timer with DAC)

time range: 30 ms, 12 ms, or 6 ms

Note: The Lenlab software automatically selects the sample rate (and time range) according to the sine frequency of the signal generator.

Note: The ADC measurement is delayed by 400 ns after the DAC changes the sample.

software trigger: synchronized with DAC, offset compensation, positive zero-crossing in the middle of the time range

peak-to-peak voltage: 3.3 V

max amplitude: 1.65 V

virtual zero at mid-level between GND and 3V3

sample window: 400 ns

## Voltmeter

logger intervals (sample rates): 20, 50, 100, 200, 500, 1000, 2000, 5000 ms (common timer with DAC)

voltage range: 0 to 3.3 V

zero level at GND

sample window: 1 ms

hardware averaging: 16 samples
