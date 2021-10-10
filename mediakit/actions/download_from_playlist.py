from pytube import Playlist
from pytube.exceptions import RegexMatchError as PytubeRegexMatchError

from mediakit import exceptions
from mediakit.actions.download import download
from mediakit.cli.arguments import command_args


def download_from_playlist():
    arguments = command_args.parse_download_arguments()

    try:
        playlist = Playlist(arguments.url)
        video_urls = playlist.video_urls

        if len(video_urls) == 0:
            raise exceptions.EmptyPlaylistException()

        download(video_urls)

    except exceptions.EmptyPlaylistException as exception:
        exception.show_message()
        return
    except PytubeRegexMatchError:
        exceptions.InvalidPlaylistURLError().show_message()
    except KeyboardInterrupt:
        pass
    except Exception as exception:
        exceptions.UnspecifiedError().show_message()
        raise exception
