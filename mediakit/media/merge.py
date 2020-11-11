from os import path

import ffmpeg

from mediakit.utils.files import increment_filename_if_exists


def merge_video_and_audio(video_path, audio_path, output_file_path):
    final_output_file_path = increment_filename_if_exists(output_file_path)

    output_filename = path.basename(video_path)
    output_format = output_filename.split('.')[-1]

    video_input = ffmpeg.input(video_path)
    audio_input = ffmpeg.input(audio_path)

    (ffmpeg
        .output(
            video_input,
            audio_input,
            final_output_file_path,
            vcodec='copy',
            f=output_format
        )
        .run(quiet=True)
    )
