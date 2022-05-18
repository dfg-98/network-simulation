#! /usr/bin/env python3

import sys

from instruction_parser import load_instructions
from simulation import Simulation


if __name__ == "__main__":

    script_path = "./script.txt"
    if len(sys.argv) > 1:
        script_path = sys.argv[1]

    instructions = load_instructions(script_path)
    simulation = Simulation()
    simulation.start(instructions)
