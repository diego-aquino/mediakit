from math import floor
from os import path

from mediakit.info import name, version
from mediakit.globals import global_config
from mediakit.utils.format import limit_text_length, parse_int
from mediakit.media.download import DownloadStatusCodes
from mediakit.cli.colors import Colors, colored
from mediakit.cli.screen import ContentCategories, screen
from mediakit.cli.download.download_cli_store import DownloadCLIStore

BYTES_PER_MEGABYTES = 1024 * 1024

LOADING_DOTS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
ROTATING_LINES = ["|", "/", "-", "\\"]


class DownloadCLIFormatter:
    def __init__(self, store: DownloadCLIStore):
        self.store = store

    def format_header(self):
        header = colored(f"{name.lower()} v{version}\n", style=Colors.style.BRIGHT)
        return header

    def format_batch_file_info_header(self, batch_filename: str):
        return (
            "\nReading URLs from "
            + colored(batch_filename, fore=Colors.fore.CYAN, style=Colors.style.BRIGHT)
            + "...\n"
        )

    def format_batch_file_info_body(self, valid_video_urls_in_batch_file):
        number_of_valid_urls = len(valid_video_urls_in_batch_file)

        return (
            "Found "
            + colored(
                f"{number_of_valid_urls} ",
                fore=Colors.fore.CYAN,
                style=Colors.style.BRIGHT,
            )
            + (
                colored("video URLs", fore=Colors.fore.CYAN)
                if number_of_valid_urls > 1
                else colored("video URL", fore=Colors.fore.CYAN)
            )
            + ". Preparing to download "
            + ("them" if number_of_valid_urls > 1 else "it")
            + (" sequentially" if number_of_valid_urls > 1 else "")
            + "...\n"
        )

    def format_video_heading(self):
        formatted_video_length = self.format_video_length()

        remaining_number_of_characters = (
            min(screen.get_console_width(), self.store.MAX_SCREEN_WIDTH)
            - len(formatted_video_length)
            - 4
        )

        formatted_video_title = self.format_video_title(remaining_number_of_characters)

        spaces_between_heading_components = " " * (
            min(screen.get_console_width(), self.store.MAX_SCREEN_WIDTH)
            - len(formatted_video_title)
            - len(formatted_video_length)
            - 3
        )

        video_heading = (
            "\n"
            + colored(
                formatted_video_title, fore=Colors.fore.CYAN, style=Colors.style.BRIGHT
            )
            + spaces_between_heading_components
            + colored(f"({formatted_video_length})\n\n", style=Colors.style.BRIGHT)
        )

        return video_heading

    def format_video_title(self, limit_of_characters: int = None) -> str:
        return limit_text_length(
            self.store.video.title,
            self.store.MAX_SHORT_VIDEO_TITLE_LENGTH
            if limit_of_characters is None
            else limit_of_characters,
        )

    def format_video_length(self):
        seconds_section = self.store.video.length % 60
        remaining_minutes = self.store.video.length // 60
        minutes_section = remaining_minutes % 60
        hours_section = remaining_minutes // 60

        formatted_video_length = (
            (f"{hours_section}:" if hours_section > 0 else "")
            + f"{minutes_section:0>2}:"
            + f"{seconds_section:0>2}"
        )

        return formatted_video_length

    def format_download_confirmation_prompt_message(self):
        download_confirmation_prompt = "\nConfirm download? " + colored(
            "(Y/n) ",
            fore=Colors.fore.CYAN,
        )

        return download_confirmation_prompt

    def format_download_progress_heading(
        self, download_status: str, status_character: str, status_color: str
    ):
        label = download_status.title()

        is_downloading_first_media_resource = (
            self.store.downloading_media_resource
            is self.store.media_resources_to_download[0]
        )

        should_include_starting_newline = is_downloading_first_media_resource or (
            download_status != DownloadStatusCodes.DONE
        )

        heading = (
            ("\n" if should_include_starting_newline else "")
            + colored(f"{status_character} {label} ", fore=status_color)
            + colored(f"{self.store.short_video_title} ", style=Colors.style.BRIGHT)
            + colored(
                f"{self.store.downloading_media_resource.formatted_definition}",
                fore=Colors.fore.BLUE,
                style=Colors.style.BRIGHT,
            )
        )

        return heading

    def format_download_progress_bar(self, status_color: str):
        media_resource = self.store.downloading_media_resource

        bytes_downloaded = (
            media_resource.total_size - media_resource.get_total_bytes_remaining()
        )

        progress_percentage = bytes_downloaded / media_resource.total_size
        available_width = min(screen.get_console_width(), self.store.MAX_SCREEN_WIDTH)

        formatted_bytes_downloaded = self.format_data_size(bytes_downloaded)
        formatted_total_size = self.format_data_size(media_resource.total_size)

        progress_bar_right = colored(
            f" {progress_percentage * 100:.1f}% ",
            fore=status_color,
            style=Colors.style.BRIGHT,
        ) + colored(
            f"({formatted_bytes_downloaded} / " + f"{formatted_total_size})",
            style=Colors.style.DIM,
        )

        max_progress_bar_right_width = len(
            f" 100.0% ({formatted_total_size} / {formatted_total_size})"
        )

        available_space_for_loading_bar = (
            available_width - max_progress_bar_right_width - 2
        )
        loaded_section_length = floor(
            available_space_for_loading_bar * progress_percentage
        )
        not_loaded_section_length = (
            available_space_for_loading_bar - loaded_section_length
        )

        if global_config.ui_colors_disabled:
            loaded_section_character = "#"
            not_loaded_section_character = "-"
            wrapper_characters = {
                "left": "[",
                "right": "]",
            }
        else:
            loaded_section_character = "█"
            not_loaded_section_character = "█"
            wrapper_characters = {
                "left": "",
                "right": "",
            }

        progress_bar_left = (
            "  "
            + wrapper_characters["left"]
            + colored(
                loaded_section_character * loaded_section_length, fore=status_color
            )
            + colored(
                not_loaded_section_character * not_loaded_section_length,
                style=Colors.style.DIM,
            )
            + wrapper_characters["right"]
        )

        progress_bar = progress_bar_left + progress_bar_right

        return progress_bar

    def format_current_download_progress(self):
        download_status = self.store.downloading_media_resource.download_status

        status_character, status_color = self.format_status_resources(download_status)
        heading = self.format_download_progress_heading(
            download_status, status_character, status_color
        )

        current_download_progress = heading + "\n"

        if download_status == DownloadStatusCodes.DONE:
            return current_download_progress

        progress_bar = self.format_download_progress_bar(status_color)

        current_download_progress += "\n" + progress_bar + "\n\n"

        return current_download_progress

    def format_data_size(self, size_in_bytes):
        size_in_megabytes = size_in_bytes / BYTES_PER_MEGABYTES
        return f"{size_in_megabytes:.1f} MB"

    def format_download_formats(self):
        formatted_definitions = map(
            lambda media_resource: media_resource.formatted_definition,
            self.store.media_resources_to_download,
        )
        formatted_download_formats = " ".join(formatted_definitions)
        return formatted_download_formats

    def format_status_resources(self, download_status):
        status_character, status_color = "", ""

        if download_status == DownloadStatusCodes.DOWNLOADING:
            self.store.rotating_line_frame = (self.store.rotating_line_frame + 1) % 4

            status_character = ROTATING_LINES[self.store.rotating_line_frame]
            status_color = Colors.fore.YELLOW

        if download_status == DownloadStatusCodes.CONVERTING:
            self.store.loading_dots_frame = (self.store.loading_dots_frame + 1) % 10

            status_character = LOADING_DOTS[self.store.loading_dots_frame]
            status_color = Colors.fore.CYAN

        if download_status == DownloadStatusCodes.DONE:
            status_character = "✔"
            status_color = Colors.fore.GREEN

        return status_character, status_color

    def format_available_formats(self):
        video_streams = self.store.video.streams.filter(type="video")
        audio_streams = self.store.video.streams.filter(type="audio")

        available_formats = {
            "video": set(),
            "audio": set(),
        }
        for stream in video_streams:
            if stream.resolution is not None:
                available_formats["video"].add(stream.resolution)
        for stream in audio_streams:
            available_formats["audio"].add(stream.abr)

        available_formats_sorted_by_definition = {
            "video": reversed(sorted(available_formats["video"], key=parse_int)),
            "audio": reversed(sorted(available_formats["audio"], key=parse_int)),
        }

        return available_formats_sorted_by_definition

    def format_skipped_formats_warning(self):
        formatted_skipped_formats = [
            f'[{" ".join(skipped_format)}]'
            for skipped_format in self.store.skipped_formats
        ]

        skipped_formats_message = (
            ("Formats " if len(self.store.skipped_formats) > 1 else "Format ")
            + colored(
                " ".join(formatted_skipped_formats),
                fore=Colors.fore.MAGENTA,
                style=Colors.style.BRIGHT,
            )
            + (" were " if len(self.store.skipped_formats) > 1 else " was ")
            + "not found. Skipping "
            + ("them" if len(self.store.skipped_formats) > 1 else "it")
            + "...\n"
        )

        return skipped_formats_message

    def format_fallback_replacement_summary(self):
        replacement_summaries = []
        for replaced_format in self.store.formats_replaced_by_fallback:
            base_format = replaced_format["base"]["format"]
            base_definition = replaced_format["base"]["definition"]
            fallback_format = replaced_format["fallback"]["format"]
            fallback_definition = replaced_format["fallback"]["definition"]

            formatted_base = self.format_replaced_format(base_format, base_definition)
            formatted_fallback = self.format_replaced_format(
                fallback_format, fallback_definition
            )

            replacement_summaries.append(
                "Format "
                + colored(
                    formatted_base, fore=Colors.fore.YELLOW, style=Colors.style.BRIGHT
                )
                + " is not available for this video. Falling back to "
                + colored(
                    formatted_fallback, fore=Colors.fore.BLUE, style=Colors.style.BRIGHT
                )
                + "\n"
            )

        return replacement_summaries

    def format_replaced_format(self, current_format, definition):
        return (
            "["
            + (f"{current_format} " if current_format != "videoaudio" else "")
            + f"{definition}]"
        )
