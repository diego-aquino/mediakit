from os import path

from mediakit.utils.files import increment_filename_if_exists
from mediakit.utils.commands import run_command_in_background
from mediakit.constants import FFMPEG_BINARY


def merge_video_and_audio(video_path, audio_path, output_file_path):
    final_output_file_path = increment_filename_if_exists(output_file_path)

    output_format = path.basename(video_path).split('.')[-1]

    command = (
        f'{FFMPEG_BINARY} -i {video_path} -i {audio_path} '
        f'-vcodec copy -f {output_format} '
        f'"{final_output_file_path}"'
    )

    run_command_in_background(command)
