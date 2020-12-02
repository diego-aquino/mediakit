from os import path

from mediakit.utils.files import increment_filename_if_exists
from mediakit.utils.commands import run_command_in_background
from mediakit.constants import FFMPEG_BINARY


VIDEO_FORMATS = { 'mp4' }


class ConversionOptions:
    NO_AUDIO = '-an'


def merge_video_and_audio(
    video_path,
    audio_path,
    output_file_path,
    output_format='mp4'
):
    final_output_file_path = increment_filename_if_exists(output_file_path)

    command = (
        f'{FFMPEG_BINARY} -i "{video_path}" -i "{audio_path}" '
        f'-vcodec copy -f {output_format} '
        f'"{final_output_file_path}"'
    )

    run_command_in_background(command)


def convert_media(file_path, output_file_path, output_format, options=[]):
    final_output_file_path = increment_filename_if_exists(output_file_path)

    command = (
        f'{FFMPEG_BINARY} -i "{file_path}" '
        + ('-vcodec copy ' if output_format in VIDEO_FORMATS else '')
        + f'-f {output_format} '
        + f'"{final_output_file_path}" '
        + ' '.join(options)
    )

    run_command_in_background(command)
