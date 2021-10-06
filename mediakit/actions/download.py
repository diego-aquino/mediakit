from os import path

from pytube.exceptions import RegexMatchError as PytubeRegexMatchError

from mediakit.cli.arguments import command_args
from mediakit.cli.download import DownloadCLI
from mediakit.utils.files import (
    get_filename_from,
    read_video_urls_from,
    file_exists,
    remove_all_temporary_files,
)
from mediakit.globals import global_config
from mediakit import exceptions


def _get_video_urls_to_download(arguments):
    was_batch_file_provided = global_config.batch_file is not None

    if not was_batch_file_provided:
        return [arguments.video_url]

    if not file_exists(global_config.batch_file):
        raise exceptions.NoSuchFile(global_config.batch_file)

    video_urls_to_download = read_video_urls_from(global_config.batch_file)

    if len(video_urls_to_download) == 0:
        raise exceptions.NoVideoURLsInBatchFile(global_config.batch_file)

    return video_urls_to_download


def download():
    arguments = command_args.parse_download_arguments()

    try:
        video_urls_to_download = _get_video_urls_to_download(arguments)
    except (exceptions.NoSuchFile, exceptions.NoVideoURLsInBatchFile) as exception:
        exception.show_message()
        return

    output_path = path.abspath(arguments.output_path)
    filename = get_filename_from(output_path)
    if filename:
        output_path = path.dirname(output_path)

    download_cli = DownloadCLI(output_path, filename)

    try:
        download_cli.start(video_urls_to_download, arguments.formats)
        download_cli.download_all()
    except exceptions.NoAvailableSpecifiedFormats as exception:
        exception.show_message()
    except PytubeRegexMatchError:
        download_cli.mark_as_loading(False)
        exceptions.InvalidVideoURLError().show_message()
    except KeyboardInterrupt:
        download_cli.terminate()
    except Exception as exception:
        download_cli.mark_as_loading(False)
        exceptions.UnspecifiedError().show_message()
        raise exception
    finally:
        remove_all_temporary_files(output_path)
        download_cli.terminate()
