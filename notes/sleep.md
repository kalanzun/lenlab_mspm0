# Sleep

2024-07-16

For continuous measurement over a long time with the voltmeter logger,
Lenlab shall prevent the system from switching in a sleep mode that would interrupt the measurement.

## Prevent sleep mode on Windows

```C
SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED);
```

https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate

```python
import ctypes

ES_CONTINUOUS = 0x80000000
ES_DISPLAY_REQUIRED = 0x00000002
ES_SYSTEM_REQUIRED = 0x00000001

# prevent sleep mode (display may still go off)
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)

# reset flag
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
```
