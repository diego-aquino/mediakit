from threading import Thread
from time import sleep
from math import floor

from mediakit.info import name, version
from mediakit.streams.screen import screen, ContentCategories
from mediakit.streams.colors import colored, Colors
from mediakit.media.download import MediaResource, DownloadStatusCodes
from mediakit.utils.format import limit_text_length
from mediakit.constants import VIDEO_RESOLUTIONS, VIDEO_RESOLUTIONS_ALIASES
from mediakit import exceptions

loading_dots = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
rotating_lines = ['|', '/', '-', '\\']


class DownloadCLI:
    def __init__(self):
        self.max_width = 80

        self.loading_label = None

        self.video = None
        self.output_path = None
        self.filename = None
        self.short_video_title = None

        self.available_formats = []
        self.media_resources_to_download = []
        self.skipped_formats = []
        self.formats_replaced_by_fallback = []

        self.downloading_media_resource = None
        self.download_progress_ui = None
        self.rotating_line_frame = 0
        self.loading_dots_frame = 0

        self.ui_update_intervals = {
            DownloadStatusCodes.DOWNLOADING: 0.2,
            DownloadStatusCodes.CONVERTING: 0.1
        }
        self.default_ui_update_interval = 0.2
        self.progress_ui_update_interval = self.default_ui_update_interval

        self.is_terminated = False

    def start(self):
        self._show_header()

    def register_download_info(self, video, output_path, filename, formats):
        self.video = video
        self.output_path = output_path
        self.filename = filename

        self.available_formats = self._get_available_formats(video)
        self.media_resources_to_download = (
            self._get_media_resources_to_download(formats)
        )

        self.short_video_title = self._format_video_title(26)

        self.remove_loading_label()

    def show_video_heading(self):
        formatted_video_length = self._format_video_length()

        remaining_number_of_characters = (
            min(screen.get_console_width(), self.max_width)
            - len(formatted_video_length)
            - 4
        )

        formatted_video_title = (
            self._format_video_title(remaining_number_of_characters)
        )

        spaces_between = ' ' * (
            min(screen.get_console_width(), self.max_width)
            - len(formatted_video_title)
            - len(formatted_video_length)
            - 3
        )

        video_summary = (
            colored(
                formatted_video_title,
                fore=Colors.fore.CYAN,
                style=Colors.style.BRIGHT
            )
            + spaces_between
            + colored(
                f'({formatted_video_length})\n\n',
                style=Colors.style.BRIGHT
            )
        )

        screen.append_content(video_summary)

    def show_download_summary(self):
        if self.were_all_formats_skipped():
            raise exceptions.NoAvailableSpecifiedFormats(self.available_formats)

        if len(self.skipped_formats) > 0:
            self._show_skipped_formats_warning()

        if len(self.formats_replaced_by_fallback) > 0:
            self._show_fallback_replacement_summary()

        formatted_title = limit_text_length(self.video.title, 26)
        formatted_download_formats = self._get_formatted_download_formats()

        media_resource_sizes = map(
            lambda media_resource: media_resource.total_size,
            self.media_resources_to_download
        )
        total_download_size = sum(media_resource_sizes)
        formatted_download_size = self._format_data_size(total_download_size)

        is_preceded_by_format_warnings = (
            len(self.skipped_formats) > 0
            or len(self.formats_replaced_by_fallback) > 0
        )

        screen.append_content(
            ('\n' if is_preceded_by_format_warnings else '')
            + 'Ready to download '
            + colored(
                f'{formatted_title} ',
                fore=Colors.fore.CYAN,
                style=Colors.style.BRIGHT
            )
            + colored(
                f'{formatted_download_formats}\n',
                fore=Colors.fore.BLUE,
                style=Colors.style.BRIGHT
            ),
            ContentCategories.INFO
        )
        screen.append_content(
            'Total download size: '
            + colored(
                f'{formatted_download_size}\n\n',
                fore=Colors.fore.YELLOW
            ),
            ContentCategories.INFO
        )

    def ask_for_confirmation_to_download(self):
        prompt_message = (
            'Confirm download? '
            + colored(
                '(Y/n) ',
                fore=Colors.fore.CYAN,
            )
        )

        answer = screen.prompt(
            prompt_message,
            valid_inputs=['', 'y', 'n']
        )

        return answer != 'n'

    def download_selected_formats(self):
        for media_resource in self.media_resources_to_download:
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
        screen.append_content(
            colored(
                '\nSuccess! ',
                fore=Colors.fore.GREEN
            )
            + 'Files saved at '
            + colored(
                f'{self.output_path}/\n\n',
                fore=Colors.fore.CYAN,
            )
        )

    def terminate(self):
        self.is_terminated = True

    def remove_loading_label(self):
        if self.loading_label is not None:
            screen.remove_content(self.loading_label)

    def were_all_formats_skipped(self):
        return (
            len(self.media_resources_to_download) == 0
            and len(self.skipped_formats) > 0
        )

    def _show_header(self):
        screen.append_content(colored(
            f'{name.lower()} v{version}\n\n',
            style=Colors.style.BRIGHT
        ))

        self.loading_label = screen.append_content(
            'Loading video.\n\n',
            ContentCategories.INFO
        )

        number_of_dots = 1

        def run_loading_animation():
            nonlocal number_of_dots

            while self.video is None and not self.is_terminated:
                number_of_dots = (number_of_dots + 1) % 4

                if self.loading_label is None:
                    break

                screen.update_content(
                    self.loading_label,
                    'Loading video' + '.' * number_of_dots + '\n\n'
                )

                sleep(0.4)

        Thread(target=run_loading_animation).start()

    def _get_media_resources_to_download(self, formats):
        if len(formats) == 0:
            default_media_resource = MediaResource(
                self.video,
                'video/audio',
                output_path=self.output_path,
                filename=self.filename
            )

            return [default_media_resource]

        media_resources_to_download = []

        should_append_format_to_filename = len(formats) > 1
        lowecased_formats = map(
            lambda selected_format: selected_format.lower(),
            formats
        )

        for selected_format in lowecased_formats:
            available_format = self._get_available_format(selected_format)

            if available_format is None:
                self.skipped_formats.append(selected_format)
                continue

            if available_format != selected_format:
                self.formats_replaced_by_fallback.append({
                    'base': selected_format,
                    'fallback': available_format
                })

            media_resource = MediaResource(
                self.video,
                'video/audio',
                output_path=self.output_path,
                definition=available_format,
                filename=self.filename,
                filename_suffix=(
                    f'[{available_format}]'
                    if should_append_format_to_filename
                    else ''
                )
            )

            media_resources_to_download.append(media_resource)

        return media_resources_to_download

    def _get_available_format(self, base_format):
        is_valid_format = (
            base_format in VIDEO_RESOLUTIONS
            or base_format in VIDEO_RESOLUTIONS_ALIASES
            or base_format == 'max'
        )
        if not is_valid_format:
            return None

        possible_format = base_format

        while possible_format is not None:
            if self._is_format_available(possible_format):
                return possible_format

            possible_format = VIDEO_RESOLUTIONS[possible_format]['next']

        return None

    def _is_format_available(self, selected_format):
        final_format = (
            VIDEO_RESOLUTIONS_ALIASES
                .get(selected_format, selected_format)
        )

        if final_format == 'max':
            video_streams = self.video.streams.filter(type='video')

            return len(video_streams) > 0

        video_streams_with_specified_resolution = (
            self.video.streams.filter(
                type='video',
                resolution=final_format
            )
        )

        return len(video_streams_with_specified_resolution) > 0

    def _create_download_progress(self, media_resource):
        self.downloading_media_resource = media_resource

        self.download_progress_ui = screen.append_content(
            self._get_current_download_progress()
        )

    def _update_download_progress_ui(self):
        screen.update_content(
            self.download_progress_ui,
            self._get_current_download_progress()
        )

    def _keep_download_progress_ui_updated(self):
        while self.downloading_media_resource and not self.is_terminated:
            self._update_download_progress_ui()
            self._update_progress_ui_interval_if_necessary()

            sleep(self.progress_ui_update_interval)

    def _update_progress_ui_interval_if_necessary(self):
        download_status = self.downloading_media_resource.download_status
        required_interval = self.ui_update_intervals.get(
            download_status,
            self.default_ui_update_interval
        )

        if self.progress_ui_update_interval != required_interval:
            self.progress_ui_update_interval = required_interval

    def _get_current_download_progress(self):
        download_status = self.downloading_media_resource.download_status

        status_character, status_color = (
            self._get_status_resources(download_status)
        )

        heading = self._get_download_progress_heading(
            download_status,
            status_character,
            status_color
        )

        current_download_progress = heading + '\n'

        if download_status == DownloadStatusCodes.DONE:
            return current_download_progress

        progress_bar = self._get_download_progress_bar(status_color)

        current_download_progress += '\n' + progress_bar + '\n\n'

        return current_download_progress

    def _get_download_progress_heading(
        self,
        download_status,
        status_character,
        status_color
    ):
        label = download_status.title()

        is_downloading_first_media_resource = (
            self.downloading_media_resource
            is self.media_resources_to_download[0]
        )

        should_include_starting_newline = (
            is_downloading_first_media_resource
            or (download_status != DownloadStatusCodes.DONE)
        )

        heading = (
            ('\n' if should_include_starting_newline else '')
            + colored(
                f'{status_character} {label} ',
                fore=status_color
            )
            + colored(
                f"{self.short_video_title} ",
                style=Colors.style.BRIGHT
            )
            + colored(
                f'{self.downloading_media_resource.formatted_definition}',
                fore=Colors.fore.BLUE,
                style=Colors.style.BRIGHT
            )
        )

        return heading

    def _get_download_progress_bar(self, status_color):
        media_resource = self.downloading_media_resource

        bytes_downloaded = (
            media_resource.total_size
            - media_resource.get_total_bytes_remaining()
        )

        progress_percentage = bytes_downloaded / media_resource.total_size
        available_width = min(screen.get_console_width(), self.max_width)

        formatted_bytes_downloaded = self._format_data_size(bytes_downloaded)
        formatted_total_size = self._format_data_size(media_resource.total_size)

        progress_bar_right = (
            colored(
                f' {progress_percentage * 100:.1f}% ',
                fore=status_color,
                style=Colors.style.BRIGHT
            )
            + colored(
                f'({formatted_bytes_downloaded} / '
                + f'{formatted_total_size})',
                style=Colors.style.DIM
            )
        )

        max_progress_bar_right_width = len(
            f' 100.0% ({formatted_total_size} / {formatted_total_size})'
        )

        available_space_for_loading_bar = (
            available_width - max_progress_bar_right_width - 2
        )
        loaded_section_length = floor(
            available_space_for_loading_bar * progress_percentage
        )

        progress_bar_left = (
            '  '
            + colored(
                '█' * loaded_section_length,
                fore=status_color
            )
            + colored(
                '█' * (available_space_for_loading_bar - loaded_section_length),
                style=Colors.style.DIM
            )
        )

        progress_bar = progress_bar_left + progress_bar_right

        return progress_bar

    def _format_video_length(self):
        seconds_section = self.video.length % 60
        remaining_minutes = self.video.length // 60
        minutes_section = remaining_minutes % 60
        hours_section = remaining_minutes // 60

        formatted_video_length = (
            (f'{hours_section}:' if hours_section > 0 else '')
            + f'{minutes_section:0>2}:'
            + f'{seconds_section:0>2}'
        )

        return formatted_video_length

    def _format_video_title(self, limit_of_characters):
        return limit_text_length(self.video.title, limit_of_characters)

    def _format_data_size(self, size_in_bytes):
        size_in_megabytes = size_in_bytes / 1000000

        return f'{size_in_megabytes:.1f} MB'

    def _get_formatted_download_formats(self):
        formatted_definitions = map(
            lambda media_resource: media_resource.formatted_definition,
            self.media_resources_to_download
        )

        formatted_download_formats = ' '.join(formatted_definitions)

        return formatted_download_formats

    def _get_status_resources(self, download_status):
        status_character, status_color = '', ''

        if download_status == DownloadStatusCodes.DOWNLOADING:
            self.rotating_line_frame = (
                (self.rotating_line_frame + 1) % 4
            )

            status_character = rotating_lines[self.rotating_line_frame]
            status_color = Colors.fore.YELLOW

        if download_status == DownloadStatusCodes.CONVERTING:
            self.loading_dots_frame = (
                (self.loading_dots_frame + 1) % 10
            )

            status_character = loading_dots[self.loading_dots_frame]
            status_color = Colors.fore.CYAN

        if download_status == DownloadStatusCodes.DONE:
            status_character = '✔'
            status_color = Colors.fore.GREEN

        return status_character, status_color

    def _get_available_formats(self, video):
        video_streams = video.streams.filter(type='video')

        available_formats = set()
        for stream in video_streams:
            if stream.resolution is not None:
                available_formats.add(stream.resolution)

        available_formats_sorted_by_definition = sorted(
            list(available_formats),
            key=lambda definition: int(definition[:-1])
        )

        return reversed(available_formats_sorted_by_definition)

    def _show_skipped_formats_warning(self):
        formatted_skipped_formats = ' '.join(map(
            lambda skipped_format: f'[{skipped_format}]',
            self.skipped_formats
        ))

        skipped_formats_message = (
            ('Formats ' if len(self.skipped_formats) > 1 else 'Format ')
            + colored(
                formatted_skipped_formats,
                fore=Colors.fore.MAGENTA,
                style=Colors.style.BRIGHT
            )
            + (' were ' if len(self.skipped_formats) > 1 else ' was ')
            + 'not found. Skipping '
            + ('them' if len(self.skipped_formats) > 1 else 'it')
            + '...\n'
        )

        screen.append_content(
            skipped_formats_message,
            ContentCategories.WARNING
        )

    def _show_fallback_replacement_summary(self):
        replacement_summaries = []
        for replaced_format in self.formats_replaced_by_fallback:
            replacement_summaries.append(
                'Format '
                + colored(
                    f"[{replaced_format['base']}]",
                    fore=Colors.fore.YELLOW,
                    style=Colors.style.BRIGHT
                )
                + ' is not available for this video. Falling back to '
                + colored(
                    f"[{replaced_format['fallback']}]",
                    fore=Colors.fore.BLUE,
                    style=Colors.style.BRIGHT
                )
                + '\n'
            )

        for summary in replacement_summaries:
            screen.append_content(summary, ContentCategories.WARNING)
