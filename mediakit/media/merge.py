from mediakit.utils.commands import run_command_in_background
from mediakit.utils.files import increment_filename_if_exists


def merge_video_and_audio(video_path, audio_path, output_file_path):
    final_output_file_path = increment_filename_if_exists(output_file_path)

    merge_command = (
        f'ffmpeg -i {video_path} -i {audio_path} '
        f'-vcodec copy "{final_output_file_path}"'
    )

    run_command_in_background(merge_command)
