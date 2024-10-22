import subprocess

from PySide6.QtCore import QIODeviceBase
from PySide6.QtSerialPort import QSerialPortInfo, QSerialPort


def profile():
    print("USB devices")
    subprocess.run(["powershell", "Get-PnpDevice -InstanceId 'USB*' | select Status,Class,FriendlyName,InstanceId"])

    port_infos = QSerialPortInfo.availablePorts()
    for info in port_infos:
        print("QSerialPortInfo")
        print("\tdescription", info.description())
        print("\tmanufacturer", info.manufacturer())
        print("\tportName", info.portName())
        print("\tpid", info.productIdentifier())
        print("\tvid", info.vendorIdentifier())
        print("\tserialNumber", info.serialNumber())
        print("\tsystemLocation", info.systemLocation())

        port = QSerialPort(info)
        print("QSerialPort")
        if port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
            print("\tbaudRate", port.baudRate())
            print("\tbreakEnabled", port.isBreakEnabled())
            print("\tdataBits", port.dataBits())
            print("\tdataTerminalReady", port.isDataTerminalReady())
            print("\terrorString", port.errorString())
            print("\tflowControl", port.flowControl())
            print("\tparity", port.parity())
            print("\trequestToSend", port.isRequestToSend())
            print("\tstopBits", port.stopBits())
            port.close()
        else:
            print("\terrorString", port.errorString())

        print("\n")

    print("standardBaudRates")
    for baud_rate in QSerialPortInfo.standardBaudRates():
        print("\t", baud_rate)

    print("\n")


if __name__ == "__main__":
    profile()
