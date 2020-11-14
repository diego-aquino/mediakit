import os

from imageio.plugins import ffmpeg

from mediakit.utils.commands import is_command_available


def get_ffmpeg_binary():
    ffmpeg_binary = (
        _try_global_command()
        or _try_existing_binary()
        or _try_imageio_ffmpeg()
    )

    return ffmpeg_binary


def _try_global_command():
    if is_command_available('ffmpeg'):
        return 'ffmpeg'
    if is_command_available('ffmpeg.exe'):
        return 'ffmpeg.exe'

    return None


def _try_existing_binary():
    ffmpeg_binary = os.getenv('FFMPEG_BINARY')

    if ffmpeg_binary and is_command_available(ffmpeg_binary):
        return ffmpeg_binary

    return None


def _try_imageio_ffmpeg():
    imageio_ffmpeg_binary = ffmpeg.get_exe()

    if is_command_available(imageio_ffmpeg_binary):
        return imageio_ffmpeg_binary

    return None
