from os import path, listdir
import re

from mediakit.utils.commands import run_command_in_background
from mediakit.info import temporary_filename
from mediakit.utils import regex


def file_exists(file_path):
    return path.isfile(file_path)


def move_file(file_path, new_file_path):
    move_command = f'mv "{file_path}" "{new_file_path}"'

    run_command_in_background(move_command)


def remove_file(file_path):
    remove_command = f'rm -rf "{file_path}"'

    run_command_in_background(remove_command)


def get_safe_filename(filename):
    partially_safe_filename = re.sub(r'[{}\\"\']', "", filename)
    safe_filename = re.sub(r"[/]", " ", partially_safe_filename)

    return safe_filename


def get_filename_from(file_path):
    filename_candidate = path.basename(file_path)
    valid_filename = 0 < filename_candidate.rfind(".") < len(filename_candidate) - 1

    return filename_candidate if valid_filename else ""


def increment_filename_if_exists(file_path):
    file_path_dirname = path.dirname(file_path)

    filename = get_filename_from(file_path)
    extension_start_index = filename.rfind(".")

    filename_without_extension = filename[:extension_start_index]
    extension = filename[extension_start_index + 1 :]

    final_file_path = file_path
    filename_number = 0
    while True:
        if not file_exists(final_file_path):
            return final_file_path

        filename_number += 1
        final_file_path = path.join(
            file_path_dirname,
            f"{filename_without_extension}({filename_number}).{extension}",
        )


def read_video_urls_from(batch_file_path):
    video_urls = []

    with open(batch_file_path, "r", encoding="utf-8") as batch_file:
        for line in batch_file:
            clear_line = line.strip()

            if regex.is_video_url_like(clear_line):
                video_urls.append(clear_line)

    return video_urls


def get_temporary_files(directory_path: str) -> "list[str]":
    items_in_directory = [
        path.join(directory_path, item) for item in listdir(directory_path)
    ]

    files_in_directory = filter(path.isfile, items_in_directory)

    temporary_files = filter(
        lambda file_path: get_filename_from(file_path).startswith(temporary_filename),
        files_in_directory,
    )

    return list(temporary_files)


def remove_all_temporary_files(directory_path: str) -> None:
    for temporary_filename in get_temporary_files(directory_path):
        remove_file(temporary_filename)
