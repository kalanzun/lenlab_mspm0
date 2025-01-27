# DAC

## Pins

| DAC | Pin | Launchpad |
| --- | --- | --------- |
| DAC12 | PA 15 | Pin 30 |

## Properties

The DAC runs with fixed sample rates of 100 kHz, 200 kHz, 500 kHz, or 1 MHz.
Below 100 kHz, there is only 0.5, 1, 2, 4, 8, or 16 kHz. There is no 10 kHz.

## Sine

- 4 KB memory
- 12 bits per point
- 2000 points

| sample rate | points | frequency |
| --- |--------| --- |
| 1 MHz | 100    | 10 kHz |
| 1 MHz | 1000   | 1 kHz |
| 1 MHz | 2000   | 500 Hz |
| 500 kHz | 1000   | 500 Hz |
| 500 kHz | 2000   | 250 Hz |
| 200 kHz | 800    | 250 Hz |
| 200 kHz | 2000   | 100 Hz |
