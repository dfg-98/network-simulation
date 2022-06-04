from random import random, randint
from typing import List

from physical_layer.bit import VoltageDecodification as VD
from device import Device, Host, Route, Router
from physical_layer.wire import Duplex
from physical_layer.port import Port
from config import check_config, CONFIG
from constants import SIGNAL_TIME
from datalink_layer.error_detection import get_error_detection_data
from network_layer.ip import IP
from network_layer.ip_sender import IPPacketSender


class Simulation:
    def __init__(self, output_path: str = "output"):
        check_config()
        self.instructions = []
        self.devices = {}
        self.hosts = {}
        self.ports = {}
        self.cables = []
        global SIGNAL_TIME
        SIGNAL_TIME = CONFIG["signal_time"]
        self.output_path = output_path
        self.end_delay = 2 * SIGNAL_TIME
        self.inst_index = 0
        self.time = 0

    def add_device(self, device: Device):
        print(f"Adding device {device.name}")
        if device.name in self.devices.keys():
            raise ValueError(
                f"The device name {device.name} is already taken."
            )

        self.devices[device.name] = device
        for port in device.ports.values():
            self.ports[port.name] = port

        if isinstance(device, Host):
            self.hosts[device.name] = device

    def connect(self, port_1: str, port_2: str):
        try:
            port1 = self._get_port_by_name(port_1)
            port2 = self._get_port_by_name(port_2)
        except KeyError as e:
            if port_1 not in self.ports.keys():
                raise ValueError(f"Port {port_1} does not exist.")
            if port_2 not in self.ports.keys():
                raise ValueError(f"Port {port_2} does not exist.")

        cable = Duplex(port1, port2)

        self.cables.append(cable)

    def assign_mac_addres(self, device_name, mac, interface):

        self.devices[device_name].mac_addrs[interface] = mac

    def assign_ip_addres(self, device_name, ip: IP, mask: IP, interface: int):
        """
        Asigna una dirección mac a un host.

        Parameters
        ----------
        device_name : str
            Nombre del dispositivo al cual se le asigna la dirección mac.
        mac : List[int]
            Dirección mac.
        """

        device = self.devices[device_name]
        if not isinstance(device, IPPacketSender):
            raise TypeError(f"Can not set ip to {device_name}")

        device.ips[interface] = ip
        device.masks[interface] = mask

    def send_frame(self, host_name: str, mac: List[VD], data: List[VD]):
        """
        Ordena a un host a enviar un frame determinado a una dirección mac
        determinada.

        Parameters
        ----------
        host_name : str
            Nombre del host que envía la información.
        mac : List[int]
            Mac destino.
        data : List[int]
            Frame a enviar.
        """

        size_str = f"{len(data)//8:b}"

        data_size = [VD.ZERO] * 8

        for i in range(1, len(size_str) + 1):
            data_size[-i] = VD(int(size_str[-i]))

        e_size, e_data = get_error_detection_data(
            data, CONFIG["error_detection"]
        )

        # rand = random()
        # if rand < 1e-3:
        #     ind = randint(0, len(data) - 1)
        #     data[ind] = VD((int(data[ind]) + 1) % 2)

        final_data = (
            mac
            + self.hosts[host_name].mac
            + data_size
            + e_size
            + data
            + e_data
        )

        self.send(host_name, final_data, len(final_data))

    def send_ip_package(self, host_name: str, ip_dest: IP, data: List[int]):

        if host_name not in self.hosts.keys():
            raise ValueError(f"Unknown host {host_name}")

        self.hosts[host_name].send_by_ip(ip_dest, data)

    def ping_to(self, host_name: str, ip_dest: IP):

        if host_name not in self.hosts.keys():
            raise ValueError(f"Unknown host {host_name}")

        self.hosts[host_name].send_ping_to(ip_dest)

    def send(self, host_name: str, data: List[VD], package_size: int = 8):

        if host_name not in self.devices.keys():
            raise ValueError(f"Host {host_name} does not exist.")

        host = self._get_host_by_name(host_name)
        host.send(data, package_size=package_size)

    def route(
        self, device_name: str, action: str = "reset", route: Route = None
    ):
        """
        Ejecuta una de las acciones realcionadas con las rutas: ``add``,
        ``remove``, ``reset``

        Parameters
        ----------
        device_name : str
            Nombre del dispositivo al que se le ejecuta la acción.
        action : str, optional
            Acción a ejecutar.
        route : Route, optional
            Ruta a añadir o eliminar.
        """

        router: Router = self.devices[device_name]
        if action == "add":
            router.add_route(route)
        elif action == "remove":
            router.remove_route(route)
        else:
            router.reset_routes()

    def disconnect(self, port_name: str):
        if port_name not in self.ports.keys():
            raise ValueError(f"Port {port_name} does not exist.")
        self.cables.remove(self.ports[port_name].cable)
        self._get_port_by_name(port_name).disconnect()
        print(f"Disconnect {port_name}")

    def start(self, instructions):
        """
        Comienza la simulación dada una lista de instrucciones.

        Parameters
        ----------
        instructions : List[Instruction]
            Lista de instrucciones a ejecutar en la simulación.
        """

        self.instructions = instructions
        self.time = 0
        while self.is_running:
            self.update()
        for device in self.devices.values():
            device.save_log(self.output_path)

    @property
    def is_running(self):
        """
        bool : Indica si la simulación todavía está en ejecución.
        """

        device_sending = any([d.is_active for d in self.devices.values()])
        running = self.instructions or device_sending
        if not running:
            self.end_delay -= 1
        return self.end_delay > 0

    def update(self):
        """
        Ejecuta un ciclo de la simulación actualizando el estado de la
        misma.

        Esta función se ejecuta una vez por cada milisegundo simulado.
        """
        # print(self.time, self.devices)
        current_insts = []
        while self.instructions and self.time == self.instructions[0].time:
            current_insts.append(self.instructions.pop(0))

        for instr in current_insts:
            instr.execute(self)

        for device in self.devices.values():
            device.reset()

        for host in self.hosts.values():
            host.update(self.time)

        for device in self.devices.values():
            if device not in self.hosts.values():
                device.update(self.time)

        for cable in self.cables:
            cable.update()

        self.time += 1

    def _get_port_by_name(self, port_name) -> Port:
        return self.ports[port_name]

    def _get_host_by_name(self, host_name) -> Host:
        return self.devices[host_name]
