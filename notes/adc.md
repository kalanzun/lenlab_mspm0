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
