import abc
import time
from threading import Thread
from typing import List

from simulation import Simulation
from physical_layer.hub import Hub
from physical_layer.host import Host


class Instruction(Thread, metaclass=abc.ABCMeta):
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

    def set_simulation(self, sim: Simulation):
        self.sim = sim

    @abc.abstractmethod
    def execute(self, sim: Simulation):
        """
        Ejecuta la instrucción en una simulación dada.

        """

    def run(
        self,
    ) -> None:
        time.sleep(self.time)
        self.execute(self.sim)


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

    def execute(self, sim: Simulation):
        print(f"Creating host: {self.host_name}")
        host = Host(self.host_name)
        sim.add_device(host)


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

    def __init__(self, time: int, host_name: str, data: List[int]):
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

    def execute(self, sim: Simulation):
        sim.disconnect(self.port_name)
