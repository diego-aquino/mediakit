from mediakit.actions import download
from mediakit.actions.download_from_playlist import download_from_playlist
from mediakit.cli.arguments import (
    command_args,
    GlobalArguments,
    show_help_message,
    show_current_version,
    show_arguments_not_recognized_error,
)


def get_command_actions():
    actions = []

    if command_args.has_argument(GlobalArguments.help):
        actions.append(show_help_message)
    if command_args.has_argument(GlobalArguments.version):
        actions.append(show_current_version)
    if command_args.has_video_url() or command_args.has_argument(GlobalArguments.batch):
        actions.append(download)
    elif command_args.has_playlist_url():
        actions.append(download_from_playlist)

    if len(actions) == 0:
        if len(command_args.arguments) > 0:
            actions.append(show_arguments_not_recognized_error)

        actions.append(show_help_message)

    return actions
