from argparse import ArgumentParser, RawDescriptionHelpFormatter

from mediakit.info import name, version, description
from mediakit.streams.colors import colored, Colors
from mediakit.globals import global_config

def create_argument_parser():
    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
        description=(
            colored(
                f'{name.lower()} v{version}\n',
                style=Colors.style.BRIGHT
            )
            + description
        )
    )

    return parser


def _update_global_config(arguments):
    global_config.answer_yes_to_all_questions = arguments.yes


def parse_download_arguments():
    parser = create_argument_parser()

    parser.add_argument(
        'video_url',
        help='URL of the YouTube video to download'
    )
    parser.add_argument(
        'output_path',
        nargs='?',
        default='./',
        help='Destination folder to where to save the downloads'
    )
    parser.add_argument(
        '-f',
        '--formats',
        nargs='*',
        default=[],
        help='Formats to download, separated by spaces (e.g. 1080p 720p 360p)'
    )
    parser.add_argument(
        '-y',
        '--yes',
        action='store_true',
        help='Answer "yes" to all questions beforehand'
    )

    arguments = parser.parse_args()
    _update_global_config(arguments)

    return arguments
