from os import path
from sys import stderr

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
        return [arguments.url]

    if not file_exists(global_config.batch_file):
        raise exceptions.NoSuchFile(global_config.batch_file)

    video_urls_to_download = read_video_urls_from(global_config.batch_file)

    if len(video_urls_to_download) == 0:
        raise exceptions.NoVideoURLsInBatchFile(global_config.batch_file)

    return video_urls_to_download


def download(video_urls: "list[str]" = None):
    arguments = command_args.parse_download_arguments()

    output_path = None
    download_cli = None

    try:
        video_urls_to_download = (
            _get_video_urls_to_download(arguments) if video_urls is None else video_urls
        )

        output_path = path.abspath(arguments.output_path)
        filename = get_filename_from(output_path)
        if filename:
            output_path = path.dirname(output_path)

        download_cli = DownloadCLI(output_path, filename)

        download_cli.start(video_urls_to_download, arguments.formats)
        download_cli.download_all()

    except (exceptions.NoSuchFile, exceptions.NoVideoURLsInBatchFile) as exception:
        exception.show_message()
        return
    except exceptions.NoAvailableSpecifiedFormats as exception:
        exception.show_message()
    except PytubeRegexMatchError:
        if download_cli is not None:
            download_cli.mark_as_loading(False)
        exceptions.InvalidVideoURLError().show_message()
    except KeyboardInterrupt:
        if download_cli is not None:
            download_cli.terminate()
    except Exception as exception:
        if download_cli is not None:
            download_cli.mark_as_loading(False)
        exceptions.UnspecifiedError().show_message()
        raise exception
    finally:
        if output_path is not None:
            remove_all_temporary_files(output_path)
        if download_cli is not None:
            download_cli.terminate()
