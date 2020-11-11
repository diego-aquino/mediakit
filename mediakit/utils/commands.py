from os import devnull
from shutil import which
import subprocess


def run_command_in_background(command):
    with open(devnull, 'w') as DEVNULL:
        subprocess.run(
            command,
            shell=True,
            stdout=DEVNULL,
            stderr=subprocess.STDOUT,
            check=True
        )


def is_command_available(command):
    return which(command) is not None
