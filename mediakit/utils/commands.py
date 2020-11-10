from os import devnull
from shutil import which
import subprocess

from mediakit import exceptions


def run_command_in_background(command):
    with open(devnull, 'w') as DEVNULL:
        try:
            subprocess.run(
                command,
                shell=True,
                stdout=DEVNULL,
                stderr=subprocess.STDOUT,
                check=True
            )
        except Exception:
            exception = exceptions.UnspecifiedError()
            print(exception.message)


def is_command_available(command):
    return which(command) is not None
