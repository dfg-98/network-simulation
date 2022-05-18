from functools import reduce
from typing import List

from .device import Device
from .port import Port
from .wire import Wire


class Hub(Device):
    """A Hub connects multiple ports.

    When a signal is written at a port this signal
    is retransmitted for the rest of the ports
    """

    def __init__(self, name: str, ports_count: int):
        self.current_transmitting_port = None
        self._received, self._sent = [], []
        ports = {}
        for i in range(ports_count):
            ports[f"{name}_{i+1}"] = Port(f"{name}_{i+1}", self.port_written)

        super().__init__(name, ports)

    def special_log(self, time: int, received: List[int], sent: List[int]):
        """
        Representación especial para los logs de los hubs.

        Parameters
        ----------
        time : int
            Timepo de ejecución de la simulación.
        received : List[int]
            Lista de bits recibidos por cada puerto.
        sent : List[int]
            Lista de bits enviados por cada puerto.
        """

        log_msg = f"| {time: ^10} |"
        for re, se in zip(received, sent):
            if re == "-":
                log_msg += f' {"---" : ^11} |'
            else:
                log_msg += f" {re :>4} . {se: <4} |"

        self.logs.append(log_msg)

    def save_log(self, path=""):
        with open(path + f"{self.name}.txt", "w+") as file:
            header = f'| {"Time (ms)": ^10} |'
            for port in self.ports.keys():
                header += f" {port: ^11} |"
            header_len = len(header)
            header += f'\n| {"": ^10} |'
            for port in self.ports.keys():
                header += f' {"Rece . Sent": ^11} |'
            file.write(f'{"-" * header_len}\n')
            file.write(f"{header}\n")
            file.write(f'{"-" * header_len}\n')
            file.write("\n".join(self.logs))
            file.write(f'\n{"-" * header_len}\n')

    def get_port_value(self, port_name: str):
        """
        Devuelve el valor del cable conectado a un puerto dado. En caso de no
        tener un cable conectado devuelve ``'-'``.

        Parameters
        ----------
        port_name : str
            Nombre del puerto.
        """
        port = self.ports[port_name]
        return str(port.read()) if port.wire is not None else "-"

    def update(self, time):
        super().update(time)
        if self.current_transmitting_port is not None:
            val = self.current_transmitting_port.read()
            if val is not None:
                for _, port in self.ports.items():
                    if (
                        port != self.current_transmitting_port
                        and port.wire is not None
                    ):
                        port.write(val)

        self._received = [self.get_port_value(p) for p in self.ports.keys()]

        self._sent = [self.get_port_value(p) for p in self.ports.keys()]
        self.special_log(time, self._received, self._sent)

    def connect(self, wire: Wire, port_name: str):
        if self.ports[port_name].wire is not None:
            raise ValueError(f"Port {port_name} is currently in use.")

        self.ports[port_name].connect(wire)

    def port_written(self, port: Port):
        if port.wire is not None:
            self.current_transmitting_port = port
