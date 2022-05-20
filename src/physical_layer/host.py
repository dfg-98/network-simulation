import imp
from typing import List, Tuple
from pathlib import Path

from .constants import SIGNAL_TIME
from .device import Device
from .port import Port
from .wire import Duplex
from .bit import VoltageDecodification as VD
from .physical_layer import PhysicalLayer
from .utils import from_bit_data_to_number
from .error_detection import check_frame_correction
from config import CONFIG, check_config


class Host(Device):
    """Represents a Host"""

    def __init__(self, name: str) -> None:
        port = Port(f"{name}_1")
        ports = {f"{name}_1": port}
        super().__init__(name, ports)
        self.physical_layer = PhysicalLayer(port)

        self.physical_layer.on_send_callbacks.append(
            lambda bit: self.log(self.simulation_time, "Sent", f"{bit}")
        )
        self.physical_layer.on_receive_callbacks.append(
            lambda bit: self.received_bit(bit)
        )
        self.physical_layer.on_collision_callbacks.append(
            lambda: self.log(
                self.simulation_time,
                "Collision",
                f"Waitting {self.physical_layer.time_to_send}ms to send",
            )
        )

        self.simulation_time = 0

        # Data receiving
        self.is_receiving_data = False
        self.received_data = []
        self.buffer = []
        self.frame_start_index = 0
        self.data_size = None
        self.data_error_size = None
        self.data_from = None

    @property
    def is_active(self):
        return self.physical_layer.is_active

    @property
    def port(self) -> Port:
        """Returns host's port"""
        return self.ports[self.port_name(1)]

    @property
    def str_mac(self):
        """str : Dirección mac del host."""
        if self.mac is not None:
            return "".join(map(str, self.mac))

    def send(self, data: List[List[VD]]):
        """
        Add data to be sent

        Parameters
        ----------
        data : List[List[VD]]
        """
        self.physical_layer.send(data)

    def connect(self, cable: Duplex, port_name: str):
        if self.port.cable is not None:
            raise ValueError(f"Port {port_name} is currently connected.")

        self.ports[self.port_name(1)].connect(cable)
        self.logs(self.simulation_time, "Connected")

    def disconnect(self, port_name: str):
        self.physical_layer.disconnect()
        self.log(self.simulation_time, "Disconnected")

    def update(self, time):
        super().update(time)
        self.physical_layer.update()

    def received_bit(self, bit: int):
        """
        Se ejecuta cada vez que el host recibe un bit. Procesa la información
        en el buffer para indentificar frames cuyo destino sea el host en
        cuestión.

        Parameters
        ----------
        bit : int
            Bit recibido.
        """

        self.log(self.simulation_time, "Received", f"{bit}")
        self.buffer.append(bit)

        if bit is None:
            self.is_receiving_data = False
            self.buffer = []
            self.data_from = None
            self.frame_start_index = 0
            self.data_size = 0
            return

        if self.is_receiving_data:
            received_size = len(self.buffer) - self.frame_start_index
            fsi = self.frame_start_index
            if received_size == 48:
                _from = from_bit_data_to_number(
                    self.buffer[fsi + 16 : fsi + 32]
                )
                self.data_from = str(hex(_from))[2:].upper()
                self.data_size = from_bit_data_to_number(
                    self.buffer[fsi + 32 : fsi + 40]
                )
                self.data_error_size = from_bit_data_to_number(
                    self.buffer[fsi + 40 : fsi + 48]
                )
            elif (
                received_size > 48
                and received_size
                == fsi + 48 + 8 * self.data_size + 8 * self.data_error_size
            ):
                frame, error = self.check_errors(self.buffer[fsi:])
                data = from_bit_data_to_number(
                    frame[48 : 48 + 8 * self.data_size]
                )
                hex_data = str(hex(data))[2:].upper()
                if len(hex_data) % 4 != 0:
                    rest = 4 - len(hex_data) % 4
                    hex_data = "0" * rest + hex_data
                r_data = [self.simulation_time, self.data_from, hex_data]
                if error:
                    r_data.append("ERROR")
                self.received_data.append(r_data)
                self.buffer = []

        last = self.buffer[-16:]
        if "".join(map(str, last)) == self.str_mac:
            self.is_receiving_data = True
            self.frame_start_index = len(self.buffer) - 16

    def save_log(self, path: str = ""):
        super().save_log(path=path)

        output_path = Path(path) / Path(f"{self.name}_data.txt")
        with open(output_path, "w+") as data_file:
            data = [" ".join(map(str, d)) + "\n" for d in self.received_data]
            data_file.writelines(data)

    def check_errors(self, frame) -> Tuple[List[VD], bool]:
        check_config()
        error_det_algorith = CONFIG["error_detection"]
        return check_frame_correction(frame, error_det_algorith)
