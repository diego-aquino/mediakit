from argparse import ArgumentParser, RawDescriptionHelpFormatter

from mediakit.info import name, version, description
from mediakit.streams.colors import colored, Colors


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

    arguments = parser.parse_args()

    return arguments
