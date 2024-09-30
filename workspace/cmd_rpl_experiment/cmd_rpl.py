from struct import pack

from PySide6.QtCore import QIODeviceBase
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo


lorem_ipsum_4096 = b"""Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean a dapibus est. Aliquam gravida, dui quis suscipit sollicitudin, urna ligula aliquam massa, quis blandit nisl magna non tellus. Donec dui nibh, elementum eget magna nec, tempus fermentum velit. Etiam sollicitudin mattis risus, elementum imperdiet lacus sodales eu. Sed a ultricies dui. Suspendisse ut metus non tortor pellentesque posuere non vitae metus. Phasellus hendrerit tempus quam. Quisque risus nisi, pulvinar vel ipsum ac, convallis pharetra massa. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Proin ornare iaculis mi, vel posuere augue sagittis quis. Vivamus tempus porta ante, sed rhoncus augue semper ac. Duis eget ullamcorper ligula.
In tempus erat et arcu lacinia cursus. Mauris ac eros molestie, venenatis libero maximus, sodales mauris. Nam libero turpis, venenatis eget efficitur nec, euismod id diam. Duis consectetur lectus id augue fringilla, eu accumsan eros ullamcorper. Quisque bibendum ullamcorper diam id porttitor. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Donec id laoreet tortor. In ligula sem, vestibulum viverra auctor vel, lacinia sit amet libero.
Pellentesque nisl turpis, lacinia id odio eu, maximus viverra ante. Pellentesque hendrerit nunc sed ex auctor, egestas pharetra massa rhoncus. In felis mi, venenatis non viverra vel, interdum tempor eros. Aenean imperdiet volutpat tristique. Praesent venenatis accumsan dolor ac vestibulum. Donec lobortis fermentum purus at auctor. Proin ultricies purus ut ex venenatis, vitae fermentum erat ultrices. In hac habitasse platea dictumst. Vivamus fermentum varius accumsan. Mauris consectetur libero id sapien tempus viverra. Mauris faucibus bibendum aliquam. Etiam pellentesque consequat nisl ut tempus.
Nunc in nulla pellentesque, eleifend arcu vel, dictum dui. Nulla semper ligula lobortis ante elementum, vel euismod mi placerat. Fusce consequat tellus id orci vestibulum, eu posuere sapien porttitor. Ut nec dictum magna. Maecenas pretium lectus a quam blandit, et semper magna gravida. Vivamus vulputate id nisl eget consequat. Aliquam erat volutpat. Sed consequat gravida hendrerit. Curabitur odio nisl, finibus vel volutpat non, tincidunt eget mi. Cras sodales felis eu neque congue ultricies. Ut vehicula ex nec rutrum finibus. Donec venenatis tristique neque, quis laoreet magna ultrices et. Nam ullamcorper urna nulla, sit amet suscipit tortor lobortis sed. In nunc eros, sollicitudin id diam eget, commodo hendrerit libero. Nullam nec sodales libero, eu fermentum neque.
Aenean vitae dolor neque. Suspendisse vitae aliquam lacus, eget pellentesque urna. Morbi a auctor felis. Phasellus ultricies lectus urna, at condimentum lacus ornare in. Cras mollis magna a est feugiat, vel iaculis sapien aliquam. Proin eget ultricies urna. Praesent ultricies mi viverra mattis tincidunt. Fusce sit amet aliquam justo, eu maximus arcu. Nam tristique gravida dolor id fermentum. Vivamus sed ornare massa, non iaculis nisi. Fusce aliquam, diam non pharetra finibus, nunc neque vestibulum diam, sit amet rhoncus quam est egestas ligula. Vestibulum ultrices varius magna, vel dignissim arcu tempus vitae. Duis sodales ante nec interdum suscipit. Maecenas bibendum lectus dui, ut sagittis elit vehicula sit amet. Nunc ut purus leo.
Donec eu volutpat metus. Morbi purus enim, feugiat vitae semper quis, molestie at orci. Proin fermentum est in velit blandit condimentum. Integer feugiat massa lectus, nec vestibulum risus congue et. Aenean vestibulum dui ut nisi dignissim, in suscipit elit volutpat. Suspendisse quis tortor eu nulla condimentum rutrum. Nam non sapien vehicula, efficitur augue vitae, auctor ipsum. Curabitur pharetra in nibh ac finibus. In eget ante mattis, facilisis nibh suscipit, iaculis nisl.
Fusce sodales diam mollis metus congue viverra. Ut efficitur commodo nibh, id congue orci varius at. Aenean nec rhoncus arcu. Suspendisse bibendum magna vel sagittis ultricies. Nulla sit amet orci facilisis, efficitur mauris sed, ornare sapien. Nu
"""


def find_vid_pid(
    port_infos: list[QSerialPortInfo], vid: int, pid: int
) -> list[QSerialPortInfo]:
    return [
        port_info
        for port_info in port_infos
        if port_info.vendorIdentifier() == vid and port_info.productIdentifier() == pid
    ]


def read(port, n):
    while n:
        port.waitForReadyRead()
        chunk = port.read(n)
        n -= len(chunk)
        yield chunk


def echo(port, word, payload):
    assert len(word) == 4
    packet = b"LE" + pack("<h", len(payload)) + word + payload
    print("write", packet)
    port.write(packet)
    reply = b"".join(read(port, len(packet)))
    print("reply", reply)
    assert reply[4:8] == word
    assert reply[8:] == payload


def main():
    port_infos = QSerialPortInfo.availablePorts()
    matches = find_vid_pid(port_infos, 0x0451, 0xBEF3)
    assert len(matches) == 2

    aux_port_info, port_info = matches
    port = QSerialPort(port_info)
    assert port.open(QIODeviceBase.OpenModeFlag.ReadWrite)

    port.setBaudRate(4000000)

    echo(port, b"LAB!", lorem_ipsum_4096)
    echo(port, b"ECHO", b"payload.")


if __name__ == "__main__":
    main()