# DAC

## Parameters

sample rate kHz: 0.5, 1, 2, 4, 8, 16, 100, 200, 500, 1000

## Requirements

range (for Bode): 100 Hz - 10 kHz

extended range: 100 Hz - 100 kHz

frequency resolution: min 50 points per decade, better 100 points per decade

## Design

extended maximum frequency, 10 points per period: 1 MHz / 10 = 100 kHz

maximum frequency, 100 points per period: 1 MHz / 100 = 10 kHz

minimum frequency (max memory), 1000 points per period: 1 / MHz / 1000 = 1 kHz

lower sample rate: 100 kHz

maximum frequency, 100 points per period: 100 kHz / 100 = 1 kHz

minimum frequency (max memory), 1000 points per period: 100 / kHz / 1000 = 100 Hz

Note: There is no sample rate 10 kHz. There is 16 kHz and then nothing up to 100 kHz.

With 4 KB of memory

| sample rate | size | frequency |
| 1 MHz | 100 | 10 kHz |
| 1 MHz | 1000 | 1 kHz |
| 1 MHz | 2000 | 500 Hz |
| 500 kHz | 1000 | 500 Hz |
| 500 kHz | 2000 | 250 Hz |
| 200 kHz | 800 | 250 Hz |
| 200 kHz | 2000 | 100 Hz |

sample rate switch at sine frequencies of 250 Hz and 500 Hz. Higher time resolution between 100 Hz and 1 kHz (> 800).

## Notes

const lookup table: With only 10 sample rates and 10 strides, the firmware would need many lookup tables for 100
frequencies (log spaced). (DMA strides: 1, 2, 3, 4, 5, 6, 7, 8, 9).

dynamic creation of the lookup table: It can easily create every table in the range from 100 to 1000 points.
With two sample rates (100 kHz and 1 MHz) it can address a wide frequency range from 100 Hz to 10 kHz.
With lookup tables in the range from 10 to 100 points, it can address an "extended" range from 10 kHz up to 100 kHz,
but at rather low time resolution (100 down to 10 samples per period).
