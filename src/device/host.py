from typing import List, Tuple
from pathlib import Path

from .router import Router
from network_layer.ip import IPPacket, IP
from datalink_layer.frame import Frame
from utils import (
    from_bit_data_to_hex,
    from_bit_data_to_number,
    from_number_to_bit_data,
)
from physical_layer.bit import VoltageDecodification as VD
from datalink_layer.error_detection import check_frame_correction
from config import CONFIG, check_config


class Host(Router):
    """Represents a Host"""

    def __init__(self, name: str) -> None:
        self.received_data = []
        self.received_payload = []
        super().__init__(name, 1)

    def send_ping_to(self, to_ip: IP) -> None:
        """
        Envia un paquete IP a una dirección haciendo ``ping``.

        Parameters
        ----------
        to_ip : IP
            IP destino.
        """

        self.send_ip_packet(IPPacket.ping(to_ip, self.ip))

    def send_ip_packet(
        self, packet: IPPacket, port: int = 1, ip_dest: IP = None
    ) -> None:
        self.enroute(packet)

    def save_log(self, path: str = ""):
        super().save_log(path)
        output_path = Path(path) / Path(f"{self.name}_data.txt")
        with open(output_path, "w+") as data_file:
            data = [" ".join(map(str, d)) + "\n" for d in self.received_data]
            data_file.writelines(data)

        output_path = Path(path) / Path(f"{self.name}_payload.txt")
        with open(output_path, "w+") as data_file:
            data = [
                " ".join(map(str, d)) + "\n" for d in self.received_payload
            ]
            data_file.writelines(data)

    @property
    def ip(self) -> IP:
        """IP : IP del host"""
        return self.ips[1]

    def on_frame_received(self, frame: Frame, port: str) -> None:
        frame, error = self.check_errors(frame.bit_data)
        frame = Frame(frame)
        data_from = from_bit_data_to_hex(
            from_number_to_bit_data(frame.from_mac)
        )
        hex_data = from_bit_data_to_hex(frame.data)
        r_data = [self.simulation_time, data_from, hex_data]
        if error:
            r_data.append("ERROR")
        else:
            super().on_frame_received(frame, 1)
        self.received_data.append(r_data)

    def on_ip_packet_received(
        self, packet: IPPacket, port: int = 1, frame: Frame = None
    ) -> None:
        if packet.to_ip != self.ip:
            return

        r_data = [self.simulation_time, str(packet.from_ip)]

        # Is ICMP protocol
        if packet.protocol_number == 1:
            payload_number = from_bit_data_to_number(packet.payload)
            if payload_number == 8:
                self.send_ip_packet(IPPacket.pong(packet.from_ip, self.ip))
            r_data.append(packet.icmp_payload_msg)
        else:
            hex_data = from_bit_data_to_hex(packet.payload)
            r_data.append(hex_data)
        self.received_payload.append(r_data)

    @property
    def physical_layer(self):
        return self.physical_layers[self.port_name(1)]

    @property
    def str_mac(self):
        """str : Dirección mac del host."""
        if self.mac is not None:
            return "".join(map(str, self.mac))

    def check_errors(self, frame) -> Tuple[List[VD], bool]:
        check_config()
        error_det_algorith = CONFIG["error_detection"]
        return check_frame_correction(frame, error_det_algorith)
