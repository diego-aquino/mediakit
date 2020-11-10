from os import path

from pytube import YouTube
from pytube.exceptions import RegexMatchError as PytubeRegexMatchError

from mediakit.streams.arguments import parse_download_arguments
from mediakit.streams.cli import DownloadCLI
from mediakit.utils.commands import is_command_available
from mediakit.utils.files import get_filename_from
from mediakit import exceptions


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

    try:
        if not is_command_available('ffmpeg'):
            raise exceptions.CommandUnavailable('ffmpeg')
    except exceptions.CommandUnavailable as exception:
        print(exception.message)
        return

    try:
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

    except PytubeRegexMatchError:
        exception = exceptions.InvalidVideoURLError()
        print(exception.message)

    except KeyboardInterrupt:
        is_downloading = (
            hasattr(download_cli, 'downloading_media_resource')
            and download_cli.downloading_media_resource is not None
        )
        if is_downloading:
            download_cli.end_download_progress()

    except Exception:
        exception = exceptions.UnspecifiedError()
        print(exception.message)
