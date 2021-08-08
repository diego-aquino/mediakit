from os import path

from pytube import YouTube
from pytube.exceptions import RegexMatchError as PytubeRegexMatchError

from mediakit.streams.arguments import command_args
from mediakit.streams.cli import DownloadCLI
from mediakit.utils.files import (
    get_filename_from,
    read_video_urls_from,
    file_exists
)
from mediakit.constants import FFMPEG_BINARY
from mediakit.globals import global_config
from mediakit import exceptions


def _get_video_urls_to_download(arguments):
    was_batch_file_provided = global_config.batch_file is not None

    if not was_batch_file_provided:
        return [arguments.video_url]

    if file_exists(global_config.batch_file):
        video_urls_to_download = read_video_urls_from(global_config.batch_file)

        if len(video_urls_to_download) == 0:
            raise exceptions.NoVideoURLsInBatchFile(
                global_config.batch_file
            )

        return video_urls_to_download

    else:
        raise exceptions.NoSuchFile(global_config.batch_file)


def download():
    def on_download_progress(stream, chunk, bytes_remaining):
        download_cli.update_download_progress_info(bytes_remaining)

    arguments = command_args.parse_download_arguments()

    try:
        video_urls_to_download = _get_video_urls_to_download(arguments)
    except (
        exceptions.NoSuchFile,
        exceptions.NoVideoURLsInBatchFile
    ) as exception:
        exception.show_message()
        return

    output_path = path.abspath(arguments.output_path)
    filename = get_filename_from(output_path)
    if filename:
        output_path = path.dirname(output_path)

    formats = arguments.formats

    download_cli = DownloadCLI()
    download_cli.start(video_urls_to_download)

    if not FFMPEG_BINARY:
        exceptions.FFMPEGNotAvailable().show_message()
        return

    for video_url_index in range(len(video_urls_to_download)):
        video_url = video_urls_to_download[video_url_index]
        is_last_video = video_url_index == len(video_urls_to_download) - 1

        try:
            download_cli.show_loading_label()

            video = YouTube(video_url)
            download_cli.register_download_info(
                video,
                output_path,
                filename,
                formats
            )
            download_cli.show_video_heading()
            download_cli.show_download_summary()

            if not global_config.answer_yes_to_all_questions:
                confirmed = download_cli.ask_for_confirmation_to_download()
                if not confirmed:
                    continue

            video.register_on_progress_callback(on_download_progress)

            download_cli.download_selected_formats()

            if global_config.batch_file:
                download_cli.clear_detailed_download_info_from_screen()
            if is_last_video:
                download_cli.show_success_message()

        except exceptions.NoAvailableSpecifiedFormats as exception:
            exception.show_message()
        except PytubeRegexMatchError:
            download_cli.remove_loading_label()
            exceptions.InvalidVideoURLError().show_message()
        except KeyboardInterrupt:
            download_cli.terminate()
            break
        except Exception as exception:
            download_cli.remove_loading_label()
            exceptions.UnspecifiedError().show_message()
            raise exception
        finally:
            if is_last_video:
                download_cli.terminate()
            else:
                download_cli.reset_state()
