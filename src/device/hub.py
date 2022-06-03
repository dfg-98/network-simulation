from functools import reduce
from typing import List
from pathlib import Path

from physical_layer.bit import VoltageDecodification as VD
from constants import SIGNAL_TIME
from .device import Device
from physical_layer.port import Port


class Hub(Device):
    """A Hub connects multiple ports.

    When a signal is written at a port this signal
    is retransmitted for the rest of the ports
    """

    def __init__(self, name: str, ports_count: int):
        self.current_transmitting_port = None
        self.read_time = 0
        self._received, self._sent = [], []
        ports = {}
        for i in range(ports_count):
            port = Port(f"{name}_{i+1}")
            port.write_callback = self.port_written(port)
            ports[f"{name}_{i+1}"] = port

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

        output_folder = Path(path)
        output_folder.mkdir(parents=True, exist_ok=True)
        output_path = output_folder / Path(f"{self.name}.txt")
        with open(str(output_path), "w+") as file:
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

    def get_port_value(self, port_name: str, received=True):
        """
        Devuelve el valor del cable conectado a un puerto dado. En caso de no
        tener un cable conectado devuelve ``'-'``.

        Parameters
        ----------
        port_name : str
            Nombre del puerto.
        """
        port = self.ports[port_name]
        return str(port.read(received)) if port.cable is not None else "-"

    def update(self, time):
        super().update(time)

        if self.read_time > 0:
            self.read_time -= 1

        if self.read_time == 0:
            self.special_log(time, self._received, self._sent)
            self.read_time = SIGNAL_TIME

    def port_written(self, port: Port):
        def port_write_callback():
            if self.read_time == 0:
                self.read_time = SIGNAL_TIME
            if port.cable is not None:
                value = port.read()
                self._received = [
                    self.get_port_value(p) for p in self.ports.keys()
                ]

                for p in self.ports.values():
                    if p != port and p.cable is not None:
                        p.write(value)
                self._sent = [
                    self.get_port_value(p, False) for p in self.ports.keys()
                ]

        return port_write_callback
