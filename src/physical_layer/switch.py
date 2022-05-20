from typing import Dict, List
from pathlib import Path


from .bit import VoltageDecodification as VD
from .constants import SIGNAL_TIME
from .device import Device
from .port import Port
from .physical_layer import PhysicalLayer
from .utils import from_bit_data_to_number
from .wire import Duplex


class Switch(Device):
    """Represents a switch"""

    def __init__(self, name, ports_count) -> None:

        ports = {}
        self.physical_layers = {}
        self.ports_buffer = {}
        for i in range(ports_count):
            port = Port(f"{name}_{i+1}")
            ports[f"{name}_{i+1}"] = port
            pl = PhysicalLayer(port)
            self.physical_layers[f"{name}_{i+1}"] = pl

            pl.on_receive_callbacks.append(
                self.receive_callback_generator(port.name)
            )
            self.ports_buffer[f"{name}_{i+1}"] = []

        self.mac_table: Dict[int, str] = {}
        super().__init__(name, ports)

    def receive_callback_generator(self, port):
        def receive_callback(bit):
            self.receive_on_port(port, bit)

        return receive_callback

    @property
    def is_active(self):
        """Returns True if the switch is active"""
        return any([pl.is_active for pl in self.physical_layers.values()])

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

    def special_log(self, time: int, received: List[VD], sent: List[VD]):
        """
        Representación especial para los logs de los switch.

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
        for bit_re, bit_se in zip(received, sent):
            if bit_re == "-" and bit_se == "-":
                log_msg += f' {"---" : ^11} |'
            else:
                log_msg += f" {bit_re :>4} . {bit_se: <4} |"
        self.logs.append(log_msg)

    def broadcast(self, from_port, data):
        """Envia un frame por todos los puertos.

        Parameters
        ----------
        from_port : str
            Puerto del cual se transmite la información.
        data : List[List[int]]
            Frame a ser enviado.
        """

        for port, pl in self.physical_layers.items():
            if port != from_port and pl.port.cable is not None:
                pl.send(data)

    def reset(self):
        pass

    def update(self, time: int):
        for pl in self.physical_layers.values():
            pl.update()

        if time % SIGNAL_TIME == 0:
            received = [self.get_port_value(p) for p in self.ports]
            sent = [self.get_port_value(p, False) for p in self.ports]
            self.special_log(time, received, sent)
        super().update(time)

    def handle_buffer_data(self, port):
        """Se encarga de procesar los datos en el buffer de un puerto.

        Parameters
        ----------
        port : str
            Nombre del puerto
        """

        data = self.ports_buffer[port]

        if len(data) < 48:
            return

        to_mac = from_bit_data_to_number(data[:16])
        from_mac = from_bit_data_to_number(data[16:32])
        size = from_bit_data_to_number(data[32:40]) * 8
        size += from_bit_data_to_number(data[40:48]) * 8

        if len(data) - 48 < size:
            return
        self.mac_table[from_mac] = port

        if to_mac in self.mac_table:
            self.physical_layers[self.mac_table[to_mac]].send([data])
        else:
            self.broadcast(port, [data])
        self.ports_buffer[port] = []

    def get_port_value(self, port_name: str, received: bool = True):
        """
        Devuelve el valor del cable conectado a un puerto dado. En caso de no
        tener un cable conectado devuelve ``'-'``.

        Parameters
        ----------
        port_name : str
            Nombre del puerto.
        """

        port = self.ports[port_name]
        bit = None
        if port.cable is not None:
            bit = port.read(received)
        return str(bit) if bit is not None else "-"

    def receive_on_port(self, port: str, bit: int):
        """Guarda el bit recibido en un puerto y procesa los datos del mismo.

        Parameters
        ----------
        port : str
            Nombre del puerto.
        bit : int
            Bit recibido
        """
        if bit == VD.NULL or bit == VD.COLLISION:
            return
        self.ports_buffer[port].append(bit)
        self.handle_buffer_data(port)

    def connect(self, cable: Duplex, port_name: str):
        port = self.ports[port_name]
        if port.cable is not None:
            raise ValueError(f"Port {port_name} is currently in use.")

        port.connect(cable)

    def disconnect(self, port_name: str):
        self.ports_buffer[list(self.ports.keys()).index(port_name)] = []
        self.physical_layers[port_name].disconnect()
