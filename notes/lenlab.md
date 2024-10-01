# Lenlab Datasheet

## Hardware

Launchpad: https://www.ti.com/tool/LP-MSPM0G3507

Microcontroller MSPM0G3507 https://www.ti.com/product/de-de/MSPM0G3507

80 MHz Arm® Cortex®-M0+ MCU mit 128 KB Flash, 32 KB SRAM, 2x4 Msps ADC, DAC, 2xOPA

## ADC

Input voltage max 3.3V (Launchpad VDD 3.3V)

### Voltmeter

Data logger, 2 channels in 2 ADC

Sample interval (s): 0.1, 0.2, 0.5, 1, 2, 5

### Oscilloscope

2 channels in 2 ADC

Samplerate 250kHz, 125kHz, 62.5kHz, ...

Resolution: 12 bit or 8 bit

Memory: 24KB

TODO: How fast can it go? Increase to 1MHz

4MHz into 24KB, 2 byte per sample is 3ms

1MHz into 24KB, 1 byte per sample is 24ms

### Bode Plotter

1 channel in 1 ADC, 100Hz to 10kHz

TODO: Is actual measurement of the DAC required (ADC1 can directly measure DAC0)?

TODO: Increase to 100kHz

## DAC

Fix on DAC_OUT (PA15)

Maximum samplerate 1MHz

Maximum sinus 100kHz

Minimum sinus 100Hz

TODO: How bad does a 10 point sinus look?
