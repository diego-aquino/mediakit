from os import devnull
from shutil import which
import subprocess

from mediakit import exceptions


def run_command_in_background(command):
    DEVNULL = open(devnull, 'w')

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
