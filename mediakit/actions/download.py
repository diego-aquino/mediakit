from os import path

from pytube import YouTube

from mediakit.streams.arguments import parse_download_arguments
from mediakit.streams.cli import DownloadCLI
from mediakit.utils.files import get_filename_from


def download():
    def on_download_progress(stream, chunk, bytes_remaining):
        download_cli.update_download_progress_info(bytes_remaining)

    arguments = parse_download_arguments()
    video_url = arguments.video_url
    output_path = path.abspath(arguments.output_path)

    filename = get_filename_from(output_path)
    if filename:
        output_path = path.dirname(output_path)

    download_cli = DownloadCLI()
    download_cli.start(video_url)

    video = YouTube(video_url)
    download_cli.register_download_info(video, output_path, filename)
    download_cli.show_video_heading()
    download_cli.show_download_summary()

    confirmed = download_cli.ask_for_confirmation_to_download()
    if not confirmed:
        return

    video.register_on_progress_callback(on_download_progress)

    download_cli.download_selected_formats()
    download_cli.show_success_message()
