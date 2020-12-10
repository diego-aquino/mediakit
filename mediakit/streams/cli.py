from os import path
from threading import Thread
from time import sleep
from math import floor

from mediakit.info import name, version
from mediakit.streams.screen import screen, ContentCategories
from mediakit.streams.colors import colored, Colors
from mediakit.media.download import MediaResource, DownloadStatusCodes
from mediakit.utils.format import limit_text_length, parse_int
from mediakit.constants import (
    DOWNLOAD_FORMATS,
    VIDEO_DEFINITIONS,
    VIDEO_DEFINITIONS_ALIASES,
    AUDIO_DEFINITIONS,
    AVAILABLE_DEFINITIONS
)
from mediakit.globals import global_config
from mediakit import exceptions

loading_dots = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
rotating_lines = ['|', '/', '-', '\\']


class DownloadCLI:
    def __init__(self):
        self.max_width = 80

        self.loading_label = None
        self.video_heading = None
        self.ready_to_download_label = None
        self.total_download_size_label = None
        self.confirm_download_prompt_message = None

        self.video = None
        self.output_path = None
        self.filename = None
        self.short_video_title = None

        self.available_formats = { 'video': [], 'audio': [] }
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

    def start(self, video_urls_to_download):
        self._show_header(video_urls_to_download)

    def show_loading_label(self):
        self.loading_label = screen.append_content(
            '\nLoading video.\n\n',
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
                    '\nLoading video' + '.' * number_of_dots + '\n\n'
                )

                sleep(0.4)

        Thread(target=run_loading_animation).start()

    def register_download_info(self, video, output_path, filename, formats):
        self.video = video
        self.output_path = output_path
        self.filename = filename

        self.available_formats = self._get_available_formats()
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

        video_heading = (
            '\n'
            + colored(
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

        self.video_heading = screen.append_content(video_heading)

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

        self.ready_to_download_label = screen.append_content(
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
        self.total_download_size_label = screen.append_content(
            'Total download size: '
            + colored(
                f'{formatted_download_size}\n',
                fore=Colors.fore.YELLOW
            ),
            ContentCategories.INFO
        )

    def ask_for_confirmation_to_download(self):
        prompt_message = (
            '\nConfirm download? '
            + colored(
                '(Y/n) ',
                fore=Colors.fore.CYAN,
            )
        )

        answer, prompt_message = screen.prompt(
            prompt_message,
            valid_inputs=['', 'y', 'n']
        )

        self.confirm_download_prompt_message = prompt_message

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

        if self.downloading_media_resource.output_type == 'videoaudio':
            if downloading_stream is self.downloading_media_resource.video:
                self.downloading_media_resource.video_bytes_remaining = (
                    bytes_remaining
                )
            elif downloading_stream is self.downloading_media_resource.audio:
                self.downloading_media_resource.audio_bytes_remaining = (
                    bytes_remaining
                )

        if self.downloading_media_resource.output_type == 'videoonly':
            self.downloading_media_resource.video_bytes_remaining = (
                bytes_remaining
            )

        if self.downloading_media_resource.output_type == 'audio':
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

    def reset_state(self):
        self.video = None
        self.output_path = None
        self.filename = None
        self.short_video_title = None

        self.available_formats = { 'video': [], 'audio': [] }
        self.media_resources_to_download = []
        self.skipped_formats = []
        self.formats_replaced_by_fallback = []

        self.downloading_media_resource = None
        self.download_progress_ui = None
        self.rotating_line_frame = 0
        self.loading_dots_frame = 0

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

    def _show_header(self, video_urls_to_download):
        screen.append_content(colored(
            f'{name.lower()} v{version}\n',
            style=Colors.style.BRIGHT
        ))

        if global_config.batch_file:
            self._show_batch_file_info(video_urls_to_download)

    def _show_batch_file_info(self, valid_video_urls_in_batch_file):
        batch_filename = path.basename(global_config.batch_file)

        number_of_valid_urls = len(valid_video_urls_in_batch_file)

        screen.append_content(
            '\nReading URLs from '
            + colored(
                batch_filename,
                fore=Colors.fore.CYAN,
                style=Colors.style.BRIGHT
            )
            + '...\n',
            ContentCategories.INFO
        )
        screen.append_content(
            'Found '
            + colored(
                f'{number_of_valid_urls} ',
                fore=Colors.fore.CYAN,
                style=Colors.style.BRIGHT
            )
            + (
                colored('video URLs', fore=Colors.fore.CYAN)
                if number_of_valid_urls > 1
                else colored('video URL', fore=Colors.fore.CYAN)
            )
            + '. Preparing to download '
            + (
                'them' if number_of_valid_urls > 1
                else 'it'
            )
            + (
                ' sequentially' if number_of_valid_urls > 1
                else ''
            )
            + '...\n',
            ContentCategories.INFO
        )

    def _get_media_resources_to_download(self, formats):
        if len(formats) == 0:
            default_media_resource = MediaResource(
                self.video,
                'videoaudio',
                output_path=self.output_path,
                filename=self.filename
            )

            return [default_media_resource]

        media_resources_to_download = []
        resources_registered_to_download = set()

        lowecased_formats = [
            selected_format.lower()
            for selected_format in formats
        ]
        grouped_formats = self._group_and_validate_formats(lowecased_formats)

        definitions_count = {}
        for group in grouped_formats:
            download_format = group['format']
            current_count = definitions_count.get(download_format, 0)
            definitions_count[download_format] = current_count + 1

        for group in grouped_formats:
            download_format = group['format']
            definition = group['definition']

            should_append_format_to_filename = (
                definitions_count[download_format] > 1
            )

            available_definition = self._get_available_definition(
                download_format,
                definition
            )

            if available_definition is None:
                self.skipped_formats.append([download_format, definition])
                continue

            if available_definition != definition:
                self.formats_replaced_by_fallback.append({
                    'base': {
                        'format': download_format,
                        'definition': definition
                    },
                    'fallback': {
                        'format': download_format,
                        'definition': available_definition
                    },
                })

            if (
                (download_format, available_definition)
                in resources_registered_to_download
            ):
                continue

            if should_append_format_to_filename:
                filename_suffix = (
                    (
                        f' [{download_format}] '
                        if download_format != 'videoaudio'
                        else ''
                    )
                    + (
                        f' [{available_definition}]'
                        if available_definition != 'max'
                        else ''
                    )
                )
            else:
                filename_suffix = ''

            media_resource = MediaResource(
                self.video,
                download_format,
                output_path=self.output_path,
                definition=available_definition,
                filename=self.filename,
                filename_suffix=filename_suffix
            )

            media_resources_to_download.append(media_resource)
            resources_registered_to_download.add(
                (download_format, available_definition)
            )

        return media_resources_to_download

    def _group_and_validate_formats(self, formats):
        grouped_formats = []

        i = 0
        while i < len(formats):
            current_item = formats[i]
            next_item = formats[i + 1] if i < len(formats) - 1 else None

            is_current_item_a_format = current_item in DOWNLOAD_FORMATS
            is_current_item_a_definition = current_item in AVAILABLE_DEFINITIONS
            is_next_item_a_format = next_item in DOWNLOAD_FORMATS
            is_next_item_a_definition = next_item in AVAILABLE_DEFINITIONS

            if is_current_item_a_format:
                if is_next_item_a_definition:
                    grouped_formats.append({
                        'format': current_item,
                        'definition': next_item
                    })
                    i += 1
                elif next_item is None or is_next_item_a_format:
                    grouped_formats.append({
                        'format': current_item,
                        'definition': 'max'
                    })
                else:
                    self.skipped_formats.append([current_item, next_item])
                    i += 1

            elif is_current_item_a_definition:
                grouped_formats.append({
                    'format': 'videoaudio',
                    'definition': current_item
                })

            else:
                self.skipped_formats.append([current_item])

            i += 1

        return grouped_formats

    def _get_available_definition(self, base_format, base_definition):
        if base_format.startswith('video'):
            is_valid_definition = (
                base_definition in VIDEO_DEFINITIONS
                or base_definition in VIDEO_DEFINITIONS_ALIASES
            )
        else:
            is_valid_definition = base_definition in AUDIO_DEFINITIONS

        if not is_valid_definition:
            return None

        possible_definition = base_definition
        while possible_definition is not None:
            if self._is_definition_available(base_format, possible_definition):
                return possible_definition

            possible_definition = (
                VIDEO_DEFINITIONS_ALIASES
                    .get(possible_definition, possible_definition)
            )

            possible_definition = (
                VIDEO_DEFINITIONS[possible_definition]['next']
                if base_format.startswith('video')
                else AUDIO_DEFINITIONS[possible_definition]['next']
            )

        return None

    def _is_definition_available(self, base_format, definition):
        if base_format.startswith('video'):
            final_definition = (
                VIDEO_DEFINITIONS_ALIASES.get(definition, definition)
            )

            if final_definition == 'max':
                video_streams = self.video.streams.filter(type='video')

                return len(video_streams) > 0

            video_streams_with_specified_resolution = (
                self.video.streams.filter(
                    type='video',
                    resolution=final_definition
                )
            )

            return len(video_streams_with_specified_resolution) > 0

        else:
            if definition == 'max':
                audio_streams = self.video.streams.filter(type='audio')

                return len(audio_streams) > 0

            audio_streams_with_specified_resolution = (
                self.video.streams.filter(
                    type='audio',
                    abr=definition
                )
            )

            return len(audio_streams_with_specified_resolution) > 0

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
        not_loaded_section_length = (
            available_space_for_loading_bar
            - loaded_section_length
        )

        if global_config.ui_colors_disabled:
            loaded_section_character = '#'
            not_loaded_section_character = '-'
            wrapper_characters = {
                'left': '[',
                'right': ']',
            }
        else:
            loaded_section_character = '█'
            not_loaded_section_character = '█'
            wrapper_characters = {
                'left': '',
                'right': '',
            }

        progress_bar_left = (
            '  '
            + wrapper_characters['left']
            + colored(
                loaded_section_character * loaded_section_length,
                fore=status_color
            )
            + colored(
                not_loaded_section_character * not_loaded_section_length,
                style=Colors.style.DIM
            )
            + wrapper_characters['right']
        )

        progress_bar = progress_bar_left + progress_bar_right

        return progress_bar

    def clear_detailed_download_info_from_screen(self):
        if self.confirm_download_prompt_message:
            screen.erase_prompt_entry(self.confirm_download_prompt_message)
            screen.remove_content(self.confirm_download_prompt_message)
        screen.remove_content(self.total_download_size_label)
        screen.remove_content(self.ready_to_download_label)
        screen.remove_content(self.video_heading)

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

    def _get_available_formats(self):
        video_streams = self.video.streams.filter(type='video')
        audio_streams = self.video.streams.filter(type='audio')

        available_formats = {
            'video': set(),
            'audio': set(),
        }
        for stream in video_streams:
            if stream.resolution is not None:
                available_formats['video'].add(stream.resolution)
        for stream in audio_streams:
            available_formats['audio'].add(stream.abr)


        available_formats_sorted_by_definition = {
            'video': reversed(
                sorted(available_formats['video'], key=parse_int)
            ),
            'audio': reversed(
                sorted(available_formats['audio'], key=parse_int)
            )
        }

        return available_formats_sorted_by_definition

    def _show_skipped_formats_warning(self):
        formatted_skipped_formats = [
            f'[{" ".join(skipped_format)}]'
            for skipped_format in self.skipped_formats
        ]

        skipped_formats_message = (
            ('Formats ' if len(self.skipped_formats) > 1 else 'Format ')
            + colored(
                ' '.join(formatted_skipped_formats),
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
        def get_formatted_replaced_format(current_format, definition):
            return (
                '['
                + (
                    f'{current_format} '
                    if current_format != 'videoaudio'
                    else ''
                )
                + f'{definition}]'
            )

        replacement_summaries = []
        for replaced_format in self.formats_replaced_by_fallback:
            base_format = replaced_format['base']['format']
            base_definition = replaced_format['base']['definition']
            fallback_format = replaced_format['fallback']['format']
            fallback_definition = replaced_format['fallback']['definition']

            formatted_base = get_formatted_replaced_format(
                base_format,
                base_definition
            )
            formatted_fallback = get_formatted_replaced_format(
                fallback_format,
                fallback_definition
            )

            replacement_summaries.append(
                'Format '
                + colored(
                    formatted_base,
                    fore=Colors.fore.YELLOW,
                    style=Colors.style.BRIGHT
                )
                + ' is not available for this video. Falling back to '
                + colored(
                    formatted_fallback,
                    fore=Colors.fore.BLUE,
                    style=Colors.style.BRIGHT
                )
                + '\n'
            )

        for summary in replacement_summaries:
            screen.append_content(summary, ContentCategories.WARNING)
