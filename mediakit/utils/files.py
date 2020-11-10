from os import path

from mediakit.utils.commands import run_command_in_background


def file_exists(file_path):
    return path.isfile(file_path)


def remove_file(file_path):
    remove_command = f'rm -rf {file_path}'

    run_command_in_background(remove_command)


def get_filename_from(file_path):
    possible_filename = path.basename(file_path)
    valid_filename = (
        0 < possible_filename.rfind('.') < len(possible_filename) - 1
    )

    return possible_filename if valid_filename else ''


def increment_filename_if_exists(file_path):
    file_path_dirname = path.dirname(file_path)

    filename = get_filename_from(file_path)
    extension_start_index = filename.rfind('.')

    filename_without_extension = filename[:extension_start_index]
    extension = filename[extension_start_index+1:]

    final_file_path = file_path
    filename_number = 0
    while True:
        if not file_exists(final_file_path):
            return final_file_path

        filename_number += 1
        final_file_path = path.join(
            file_path_dirname,
            f'{filename_without_extension}({filename_number}).{extension}'
        )
