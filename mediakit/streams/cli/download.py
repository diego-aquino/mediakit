from os import path
from threading import Thread
from time import sleep
from math import floor

from mediakit.info import name, version
from mediakit.streams.screen import Screen
from mediakit.media.download import MediaResource, statuscodes
from mediakit.utils.format import limit_text_length

loading_characters = ['|', '/', '-', '\\']


class DownloadCLI:
    def __init__(self):
        self.max_width = 80

    def start(self, video_url):
        self.screen = Screen()
        self.show_header(video_url)

    def show_header(self, video_url):
        self.screen.append_content(f'\n[{name} v{version}]\n\n')

        preparing_text = limit_text_length(
            f'Preparing to download video at {video_url}',
            min(self.screen.get_console_width(), self.max_width) - 3
        )
        preparing_text_end = (
            '' if preparing_text.endswith('...')
            else '...'
        )

        self.screen.append_content(f'{preparing_text}{preparing_text_end}\n\n')

    def register_download_info(self, video, output_path, filename):
        self.video = video
        self.output_path = output_path
        self.filename = filename

        self.short_video_title = self._format_video_title(26)

    def show_video_heading(self):
        formatted_video_length = self._format_video_length()

        remaining_number_of_characters = (
            min(self.screen.get_console_width(), self.max_width)
            - len(formatted_video_length)
            - 4
        )

        formatted_video_title = (
            self._format_video_title(remaining_number_of_characters)
        )

        spaces_between = ' ' * (
            min(self.screen.get_console_width(), self.max_width)
            - len(formatted_video_title)
            - len(formatted_video_length)
            - 3
        )

        video_summary = (
            formatted_video_title
            + spaces_between
            + f'({formatted_video_length})\n\n'
        )

        self.screen.append_content(video_summary)

    def show_download_summary(self):
        self.formats_to_download = [
            MediaResource(
                self.video,
                'video/audio',
                output_path=self.output_path,
                filename=self.filename
            )
        ]

        formatted_title = limit_text_length(self.video.title, 26)
        formatted_download_formats = self._get_formatted_download_formats()

        media_resource_sizes = map(
            lambda media_resource: media_resource.total_size,
            self.formats_to_download
        )
        total_download_size = sum(media_resource_sizes)
        formatted_download_size = self._format_data_size(total_download_size)

        self.screen.append_content(
            f'Ready to download {formatted_title} {formatted_download_formats}\n'
            f'Total download size: {formatted_download_size}\n\n'
        )

    def ask_for_confirmation_to_download(self):
        answer = self.screen.prompt(
            '? Confirm download? (Y/n) ',
            valid_inputs=['', 'y', 'n']
        )

        return answer != 'n'

    def download_selected_formats(self):
        for media_resource in self.formats_to_download:
            self._create_download_progress(media_resource)
            screen_thread = Thread(
                target=self._keep_download_progress_ui_updated
            )
            screen_thread.start()

            media_resource.download()

            self.end_download_progress()

    def update_download_progress_info(self, bytes_remaining):
        downloading_stream = self.downloading_media_resource.downloading_stream

        if self.downloading_media_resource.output_type == 'video/audio':
            if downloading_stream is self.downloading_media_resource.video:
                self.downloading_media_resource.video_bytes_remaining = (
                    bytes_remaining
                )
            elif downloading_stream is self.downloading_media_resource.audio:
                self.downloading_media_resource.audio_bytes_remaining = (
                    bytes_remaining
                )

        if self.downloading_media_resource.output_type == 'video-only':
            self.downloading_media_resource.video_bytes_remaining = (
                bytes_remaining
            )

        if self.downloading_media_resource.output_type == 'audio-only':
            self.downloading_media_resource.audio_bytes_remaining = (
                bytes_remaining
            )

    def end_download_progress(self):
        self._update_download_progress_ui()

        self.downloading_media_resource = None
        self.download_progress_ui = None

    def show_success_message(self):
        self.screen.append_content(
            f'Success! Files saved at {self.output_path}/\n\n'
        )

    def _create_download_progress(self, media_resource):
        self.downloading_media_resource = media_resource
        self.loading_character_index = 0

        self.download_progress_ui = self.screen.append_content(
            self._get_current_download_progress()
        )

    def _update_download_progress_ui(self):
        self.screen.update_content(
            self.download_progress_ui,
            self._get_current_download_progress()
        )

    def _keep_download_progress_ui_updated(self):
        while self.downloading_media_resource:
            self._update_download_progress_ui()
            sleep(0.2)

    def _get_current_download_progress(self):
        media_resource = self.downloading_media_resource

        loading_character = self._get_next_loading_character()
        download_status = self.downloading_media_resource.download_status
        label = download_status.title()

        bytes_downloaded = (
            media_resource.total_size
            - media_resource.get_total_bytes_remaining()
        )

        progress_percentage = bytes_downloaded / media_resource.total_size

        available_width = min(self.screen.get_console_width(), self.max_width)

        line_1 = {
            'left': (
                f'\n{loading_character} '
                f"{label} '{self.short_video_title}' "
                f'{media_resource.formatted_definition}'
            ),
            'right': f'({progress_percentage * 100:.1f}%)'
        }

        available_spaces_in_between = max(
            available_width - len(line_1['left']) - len(line_1['right']),
            5
        )
        line_1['middle'] = ' ' * available_spaces_in_between

        line_2 = {
            'right': (
                f'[{self._format_data_size(bytes_downloaded)} / '
                f'{self._format_data_size(media_resource.total_size)}]'
            )
        }
        available_space_for_loading_bar = (
            available_width - len(line_2['right']) - 3
        )
        loaded_section_length = floor(
            available_space_for_loading_bar * progress_percentage
        )
        line_2['left'] = (
            '['
            + "#" * loaded_section_length
            + "-" * (available_space_for_loading_bar - loaded_section_length)
            + ']'
        )

        current_download_progress = (
            line_1['left'] + line_1['middle'] + line_1['right'] + '\n'
            + line_2['left'] + line_2['right'] + '\n\n'
        )

        return current_download_progress

    def _format_video_length(self):
        seconds_section = self.video.length % 60
        remaining_minutes = self.video.length // 60
        minutes_section = remaining_minutes % 60
        hours_section = remaining_minutes // 60

        formatted_video_length = (
            f'{hours_section}:' if hours_section > 0 else ''
            + f'{minutes_section:0>2}:'
            + f'{seconds_section:0>2}')

        return formatted_video_length

    def _format_video_title(self, limit_of_characters):
        return limit_text_length(self.video.title, limit_of_characters)

    def _format_data_size(self, size_in_bytes):
        size_in_megabytes = size_in_bytes / 1000000

        return f'{size_in_megabytes:.1f} MB'

    def _get_formatted_download_formats(self):
        formatted_definitions = map(
            lambda media_resource: media_resource.formatted_definition,
            self.formats_to_download
        )

        formatted_download_formats = ' '.join(formatted_definitions)

        return formatted_download_formats

    def _get_next_loading_character(self):
        self.loading_character_index = (self.loading_character_index + 1) % 4

        return loading_characters[self.loading_character_index]
