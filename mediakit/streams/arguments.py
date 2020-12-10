import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from mediakit.info import name, version, description
from mediakit.utils import regex
from mediakit.streams.colors import colored, Colors
from mediakit.streams.screen import screen, ContentCategories
from mediakit.globals import global_config


class GlobalArguments:
    help = ['-h', '--help']
    yes = ['-y', '--yes']
    version = ['-v', '--version']
    no_colors = ['-nc', '--no-colors']
    batch = ['-b', '--batch']


class Parser(ArgumentParser):
    def add_global_arguments(self):
        self.add_argument(
            *GlobalArguments.help,
            action='store_true',
            help='Show this help message'
        )
        self.add_argument(
            *GlobalArguments.yes,
            action='store_true',
            help='Answer "yes" to all questions beforehand'
        )
        self.add_argument(
            *GlobalArguments.version,
            action='store_true',
            help='Show the current version'
        )
        self.add_argument(
            *GlobalArguments.no_colors,
            dest='no_colors',
            action='store_true',
            help='Disable the colors of the interface'
        )
        self.add_argument(
            *GlobalArguments.batch,
            nargs=1,
            help='Download videos from URLs stored in a batch file'
        )

    def add_download_arguments(self):
        if not global_config.batch_file:
            self.add_argument(
                'video_url',
                help='URL of the YouTube video to download'
            )
        self.add_argument(
            'output_path',
            nargs='?',
            default='./',
            help='Destination folder to where to save the downloads'
        )
        self.add_argument(
            '-f',
            '--formats',
            nargs='*',
            default=[],
            help='Formats to download, separated by spaces (e.g. 1080p 720p 360p)'
        )


def update_global_config_based_on_arguments(arguments):
    answer_yes_to_all_questions = getattr(
        arguments,
        'yes',
        global_config.answer_yes_to_all_questions
    )
    ui_colors_disabled = getattr(
        arguments,
        'no_colors',
        global_config.ui_colors_disabled
    )
    batch_file = getattr(
        arguments,
        'batch',
        global_config.batch_file
    )

    global_config.answer_yes_to_all_questions = answer_yes_to_all_questions
    global_config.ui_colors_disabled = ui_colors_disabled

    was_batch_file_provided = (
        isinstance(batch_file, list)
        and len(batch_file) == 1
    )
    global_config.batch_file = (
        batch_file[0] if was_batch_file_provided
        else global_config.batch_file
    )


class CommandArgs:
    def __init__(self, args=sys.argv, parse_and_update_global_config=True):
        self.arguments = args[1:]
        self.unique_arguments = set(self.arguments)

        self.parser = Parser(
            formatter_class=RawDescriptionHelpFormatter,
            add_help=False
        )

        self.parser.add_global_arguments()
        self.global_arguments = self.parser.parse_known_args()[0]
        if parse_and_update_global_config:
            update_global_config_based_on_arguments(self.global_arguments)

        self.parser.description = (
            colored(
                f'{name.lower()} v{version}\n',
                style=Colors.style.BRIGHT
            )
            + description
        )

    def has_argument(self, possible_arguments):
        intersection = (
            self.unique_arguments
                .intersection(set(possible_arguments))
        )

        return len(intersection) > 0

    def has_video_url(self):
        for argument in self.unique_arguments:
            if regex.is_video_url_like(argument):
                return True

        return False


    def parse_download_arguments(self):
        self.parser.add_download_arguments()

        arguments = self.parser.parse_args()

        return arguments


def show_current_version():
    screen.append_content(f'{version}\n')


def show_help_message():
    command_args.parser.add_download_arguments()
    screen.append_content(
        command_args.parser.format_help()
    )


def show_arguments_not_recognized_error():
    screen.append_content(
        '\nCould not recognize the provided arguments. '
        + 'Please check your entries and try again.\n\n',
        ContentCategories.ERROR
    )


command_args = CommandArgs()
