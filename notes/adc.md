# ADC

## Pins

| ADC  | ADC channel | Pin   | Launchpad |
|------|-------------|-------|-----------|
| ADC0 | channel 3   | PA 24 | Pin 27    |
| ADC1 | channel 2   | PA 17 | Pin 28    |

Note: PA18 is the button S1 to boot the BSL

## SysConfig

ADC configuration for continuous timer events

- Conversion Mode: Single
- Enable Repeat Mode: True
- Trigger Mode: Valid trigger will step to next memory conversion register

## Mode change

Oscilloscope mode or voltmeter mode.

Voltmeter does not enable DMA, but fetches the values from the FIFO in the interrupt handler.

Different sample window duration:

```c
DL_ADC12_setSampleTime0(ADC12_CH1_INST,8); // 400 ns
DL_ADC12_setSampleTime0(ADC12_CH1_INST,20000); // 1 ms
```

Voltmeter triggers the ADC slowly, oscilloscope quickly.

Both modes use the same memory, as memory is limited.
