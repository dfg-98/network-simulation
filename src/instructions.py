from __future__ import annotations
import abc
from typing import List

from physical_layer.bit import VoltageDecodification as VD
from network_layer.ip import IP
from device import Host, Hub, Switch, Router, Route


class Instruction(metaclass=abc.ABCMeta):
    """
    Representación general de una instrucción.

    Parameters
    ----------
    time : int
        Timepo en milisegundos en el que será ejecutada la instrucción en
        la simulación.
    """

    def __init__(self, time: int):
        super().__init__()
        self.time = time

    @abc.abstractmethod
    def execute(self, sim: "Simulation"):
        """
        Ejecuta la instrucción en una simulación dada.

        """


class CreateHubIns(Instruction):
    """
    Instrucción para crear un Hub.

    Parameters
    ----------
    time : int
        Timepo en milisegundos en el que será ejecutada la instrucción en
        la simulación.
    hub_name : str
        Nombre del hub.
    ports_count : int
        Cantidad de puertos del hub.
    """

    def __init__(self, time: int, hub_name: str, ports_count: int):
        super().__init__(time)
        self.hub_name = hub_name
        self.ports_count = ports_count

    def execute(self, sim: Simulation):
        print(f"Creating hub: {self.hub_name}")
        hub = Hub(self.hub_name, self.ports_count)
        sim.add_device(hub)


class CreateHostIns(Instruction):
    """
    Instrucción para crear un Host.

    Parameters
    ----------
    time : int
        Timepo en milisegundos en el que será ejecutada la instrucción en
        la simulación.
    host_name : str
        Nombre del host.
    """

    def __init__(self, time: int, host_name: str):
        super().__init__(time)
        self.host_name = host_name

    def execute(self, sim: "Simulation"):
        print(f"Creating host: {self.host_name}")
        host = Host(self.host_name)
        sim.add_device(host)


class CreateRouterIns(Instruction):
    """
    Instrucción para crear un Router.

    Parameters
    ----------
    time : int
        Timepo en milisegundos en el que será ejecutada la instrucción en
        la simulación.
    host_name : str
        Nombre del host.
    """

    def __init__(self, time: int, router_name: str, ports_count: int):
        super().__init__(time)
        self.router_name = router_name
        self.ports_count = ports_count

    def execute(self, sim: "Simulation"):
        print(
            f'[{self.time:>6}] Creating Router {self.router_name} with {self.ports_count} port{("s" if self.ports_count > 1 else "")}'
        )
        router = Router(self.router_name, self.ports_count)
        sim.add_device(router)


class ConnectIns(Instruction):
    """
    Instrucción para conectar dos puertos.

    Parameters
    ----------
    time : int
        Timepo en milisegundos en el que será ejecutada la instrucción en
        la simulación.
    port1, port2 : str
        Nombre de los puertos a conectar.
    """

    def __init__(self, time: int, port1: str, port2: str):
        super().__init__(time)
        self.port1 = port1
        self.port2 = port2

    def execute(self, sim: Simulation):
        print(f"Connecting: {self.port1} - {self.port2}")
        sim.connect(self.port1, self.port2)


class SendIns(Instruction):
    """
    Instrucción para ordenar a un host a enviar información.

    Parameters
    ----------
    time : int
        Timepo en milisegundos en el que será ejecutada la instrucción en
        la simulación.
    host_name : str
        Nombre del host que enviará los datos.
    data : List[int]
        Datos a enviar.
    """

    def __init__(self, time: int, host_name: str, data: List[VD]):
        super().__init__(time)
        self.host_name = host_name
        self.data = data

    def execute(self, sim: Simulation):
        sim.send(self.host_name, self.data)


class DisconnectIns(Instruction):
    """
    Instrucción para desconectar un puerto.

    Parameters
    ----------
    time : int
        Timepo en milisegundos en el que será ejecutada la instrucción en
        la simulación.
    port_name : str
        Nombre del puerto al que se le desconectará el cable.
    """

    def __init__(self, time: int, port_name: str):
        super().__init__(time)
        self.port_name = port_name

    def execute(self, sim: "Simulation"):
        sim.disconnect(self.port_name)


class CreateSwitchIns(Instruction):
    """
    Instrucción para crear un Switch.

    Parameters
    ----------
    time : int
        Timepo en milisegundos en el que será ejecutada la instrucción en
        la simulación.
    switch_name : str
        Nombre del switch.
    ports_count : int
        Cantidad de puertos del switch.
    """

    def __init__(self, time: int, switch_name: str, ports_count: int):
        super().__init__(time)
        self.switch_name = switch_name
        self.ports_count = ports_count

    def execute(self, sim: "Simulation"):
        switch = Switch(self.switch_name, self.ports_count)
        sim.add_device(switch)


class MacIns(Instruction):
    def __init__(
        self, time: int, host_name: str, interface: int, address: List[int]
    ):
        super().__init__(time)
        self.host_name = host_name
        self.address = address
        self.interface = interface

    def execute(self, sim: "Simulation"):
        sim.assign_mac_addres(self.host_name, self.address, self.interface)


class IPIns(Instruction):
    def __init__(
        self, time: int, device_name: str, interface: int, ip: IP, mask: IP
    ):
        super().__init__(time)
        self.device_name = device_name
        self.ip = ip
        self.mask = mask
        self.interface = interface

    def execute(self, sim: "Simulation"):
        sim.assign_ip_addres(
            self.device_name, self.ip, self.mask, self.interface
        )


class SendFrameIns(Instruction):
    def __init__(
        self, time: int, host_name: str, mac: List[VD], data: List[VD]
    ):
        super().__init__(time)
        self.host_name = host_name
        self.mac = mac
        self.data = data

    def execute(self, sim: "Simulation"):
        sim.send_frame(self.host_name, self.mac, self.data)


class SendIPPackage(Instruction):
    def __init__(self, time: int, host_name: str, ip_dest: IP, data: List[VD]):
        super().__init__(time)
        self.host_name = host_name
        self.ip = ip_dest
        self.data = data

    def execute(self, sim: "Simulation"):
        sim.send_ip_package(self.host_name, self.ip, self.data)


class PingIns(Instruction):
    def __init__(
        self,
        time: int,
        host_name: str,
        ip_dest: IP,
    ):
        super().__init__(time)
        self.host_name = host_name
        self.ip = ip_dest

    def execute(self, sim: "Simulation"):
        sim.ping_to(self.host_name, self.ip)


class RouteIns(Instruction):
    def __init__(
        self,
        time: int,
        device_name: str = None,
        action: str = "reset",
        destination_ip: IP = None,
        mask: IP = None,
        gateway: IP = None,
        interface: int = None,
    ):
        super().__init__(time)
        self.action = action
        self.device_name = device_name
        self.route = None

        if (
            destination_ip is not None
            and mask is not None
            and gateway is not None
            and interface is not None
        ):
            self.route = Route(destination_ip, mask, gateway, interface)

    def execute(self, sim: "Simulation"):
        sim.route(self.device_name, self.action, self.route)
