from nesim.devices.ip_packet_sender import IPPacketSender
from nesim.devices.utils import (
    from_bit_data_to_number,
    from_number_to_bit_data,
    from_str_to_bin,
)
from typing import List, Union
from nesim.devices.multiple_port_device import MultiplePortDevice
from nesim.frame import Frame
from nesim.ip import IP, IPPacket


class Route:
    def __init__(
        self, destination_ip: IP, mask: IP, gateway: IP, interface: int
    ) -> None:
        self.destination_ip = destination_ip
        self.mask = mask
        self.gateway = gateway
        self.interface = interface

    def enroute(self, ip: IP) -> bool:
        masked_ip = ip.raw_value & self.mask.raw_value
        if masked_ip == self.destination_ip.raw_value:
            return True
        return False

    def __eq__(self, other: object) -> bool:
        return (
            self.destination_ip == other.destination_ip
            and self.mask == other.mask
            and self.gateway == other.gateway
            and self.interface == other.interface
        )

    def __str__(self) -> str:
        return f"{self.destination_ip} {self.mask} {self.gateway} {self.interface}"


class RouteTable:
    """Tabla de rutas"""

    def __init__(self) -> None:
        self.routes: List[Route] = []

    def reset_routes(self) -> None:
        """Limpia la tabla de rutas."""

        self.routes.clear()

    def add_route(self, route: Route) -> None:
        """
        Agrega una ruta a la tabla de rutas.

        Parameters
        ----------
        route : Route
            Ruta a añadir.
        """

        self.routes.append(route)
        self.routes.sort(key=lambda x: x.mask.raw_value, reverse=True)

    def remove_route(self, route: Route) -> None:
        """
        Elimina una ruta de la tabla de rutas.

        Parameters
        ----------
        route : Route
            Ruta a eliminar.
        """

        if route in self.routes:
            self.routes.remove(route)

    def get_enrouting(self, ip: IP) -> Union[Route, None]:
        """
        Obtiene la ruta según la prioridad de las mismas dado un IP.

        Parameters
        ----------
        ip : IP
            Ip a enrutar.

        Returns
        -------
        Union[Route, None]
            Ruta obtenida. None en caso de no existir ninguna ruta.
        """

        for route in self.routes:
            if route.enroute(ip):
                return route
        return None


class Router(IPPacketSender, RouteTable):
    """Representa un router en la simulación."""

    def __init__(self, name: str, ports_count: int, signal_time: int):
        self.routes = []
        super().__init__(name, ports_count, signal_time)

    def enroute(self, packet: IPPacket, port: int = 1, frame: Frame = None):
        """
        Enruta un paquete IP.

        Parameters
        ----------
        packet : IPPacket
            Paquete a enrutar.
        port : int, optional
            Puerto por el cual sale el paquete (interfase), por defecto 1.
        frame : Frame, optional
            Frame que contiene al paquete, por defecto None.
        """

        route = self.get_enrouting(packet.to_ip)

        if route is None and frame is not None:
            data = IPPacket.no_dest_host(
                packet.from_ip, self.ips[port]
            ).bit_data
            super().send_frame(
                from_number_to_bit_data(frame.from_mac, 16), data, port
            )
            return

        to_ip = route.gateway
        if route.gateway.raw_value == 0:
            to_ip = packet.to_ip
        super().send_ip_packet(packet, route.interface, to_ip)

    def on_ip_packet_received(
        self, packet: IPPacket, port: int = 1, frame: Frame = None
    ) -> None:
        """
        Se ejecuta cuando un packete IP es recibido.

        Parameters
        ----------
        packet : IPPacket
            Paquete recibido.
        port : int, optional
            Puerto por el cual llegó el paquete, por defecto 1.
        frame : Frame, optional
            Frame que contiene el paquete, por defecto None.
        """

        self.enroute(packet, port, frame)

    def on_frame_received(self, frame: Frame, port: int) -> None:
        print(f"[{self.sim_time:>6}] {self.name:>18}  received:", frame)
        mac_dest = from_number_to_bit_data(frame.to_mac, 16)
        mac_dest_str = "".join(map(str, mac_dest))
        mac_origin = from_number_to_bit_data(frame.from_mac, 16)
        data_s = frame.frame_data_size
        data = frame.data

        # ARPQ protocol
        if data_s / 8 == 8:
            arpq = from_str_to_bin("ARPQ")
            ip = "".join(map(str, data[32:64]))
            if mac_dest_str == "1" * 16:
                arpq_data = "".join(map(str, data[:32]))
                ip_values = [i.str_binary for i in self.ips.values()]
                if arpq_data.endswith(arpq) and ip in ip_values:
                    self.respond_arpq(mac_origin, port)
            else:
                new_ip = IP.from_bin(ip)
                self.ip_table[str(new_ip)] = mac_origin
                if str(new_ip) in self.waiting_for_arpq:
                    for data in self.waiting_for_arpq[str(new_ip)]:
                        self.send_frame(mac_origin, data, port)
                    self.waiting_for_arpq[str(new_ip)] = []
            return

        valid_packet, packet = IPPacket.parse(frame.data)
        if valid_packet:
            self.on_ip_packet_received(packet, port, frame)
