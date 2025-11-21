## Datasheet

### Voltmeter

| Parameter              | Value                                  |
| ---------------------- | -------------------------------------- |
| Channels               | 2                                      |
| Sampling interval      | 20, 50, 100, 200, 500, 1 000, 2 000 ms |
| Voltage range          | 0 to 3.3 V                             |
| Resolution             | 12 bits                                |
| ADC sample window      | 1 ms                                   |
| ADC hardware averaging | 16 samples                             |

### Oscilloscope / Bode-Plotter

| Parameter                 | Value                   |
| ------------------------- | ----------------------- |
| Channels                  | 2                       |
| Memory size (per channel) | 6 001 samples           |
| Sampling rate             | 200 kHz, 500 kHz, 1 MHz |
| Time range                | 30, 12, 6 ms            |
| Voltage range             | -1.65 to 1.65 V         |
| Resolution                | 12 bits                 |
| ADC sample window         | 400 ns                  |

*Sample Timer* The oscilloscope (ADC) and the signal generator (DAC) share one sample rate timer. So the oscilloscope operates at the sample rate chosen by the signal generator. The ADC measurement of a sample is delayed by 400 ns after the DAC outputs a new value.

*Software Trigger* The oscilloscope has a software trigger. It compensates for the time offset to the signal generator, so that the rising flank of the sine function crosses zero (zero volts on the value axis) at the mid-point (zero seconds on the time axis). If you directly connect DAC and ADC, it shows the sine function without time offset.

### Signal Generator

| Parameter                 | Value                   |
| ------------------------- | ----------------------- |
| Channels                  | 1                       |
| Function                  | Sine                    |
| Memory size (per channel) | 2 000 samples           |
| Sampling rate             | 200 kHz, 500 kHz, 1 MHz |
| Frequency range           | 100 Hz to 10 kHz        |
| Voltage range             | -1.65 to 1.65 V         |

*Sample Timer* The signal generator calculates a full period of the sine function (from 0 to 2π) and saves the samples in the memory. It then continuously outputs the samples with a fixed sample rate, which it chooses automatically according to the sine frequency and memory size.

*Overlaying two sine functions* The signal generator may overlay two sine functions. The frequency of the second sine function is an integer multiple of the first sine's frequency. The amplitude of both sine functions is the same and half the value of the amplitude setting. Because of that, the sum of both sine functions stays within the voltage range.