from os import path
from threading import Thread
from time import sleep
from pytube import YouTube

from mediakit.cli.screen import screen, ContentCategories
from mediakit.cli.colors import colored, Colors
from mediakit.media.download import MediaResource
from mediakit.utils.format import limit_text_length, parse_int
from mediakit.cli.loadble_cli import LoadableCLI
from mediakit.cli.download.download_cli_formatter import DownloadCLIFormatter
from mediakit.cli.download.download_cli_store import DownloadCLIStore
from mediakit.constants import (
    DOWNLOAD_FORMATS,
    VIDEO_DEFINITIONS,
    VIDEO_DEFINITIONS_ALIASES,
    AUDIO_DEFINITIONS,
    AVAILABLE_DEFINITIONS,
)
from mediakit.globals import global_config
from mediakit import exceptions


class DownloadCLI(LoadableCLI):
    def __init__(self):
        super().__init__(DownloadCLIStore())
        self.formatter = DownloadCLIFormatter(self.store)

    def start(self, video_urls_to_download: "list[str]"):
        self._show_header(video_urls_to_download)

    def register_download_info(
        self, video: YouTube, output_path: str, filename: str, formats: "list[str]"
    ):
        self.store.video = video
        self.store.video.register_on_progress_callback(self.handle_download_progress)

        self.store.output_path = output_path
        self.store.filename = filename

        self.store.available_formats = self._get_available_formats()
        self.store.media_resources_to_download = self._get_media_resources_to_download(
            formats
        )

        self.store.short_video_title = self.formatter.format_video_title()

    def show_video_heading(self):
        formatted_video_heading = self.formatter.format_video_heading()
        self.store.video_heading = screen.append_content(formatted_video_heading)

    def show_download_summary(self):
        if self.were_all_formats_skipped():
            raise exceptions.NoAvailableSpecifiedFormats(self.store.available_formats)

        if len(self.store.skipped_formats) > 0:
            self._show_skipped_formats_warning()

        if len(self.store.formats_replaced_by_fallback) > 0:
            self._show_fallback_replacement_summary()

        formatted_title = limit_text_length(self.store.video.title, 26)
        formatted_download_formats = self.formatter.format_download_formats()

        media_resource_sizes = map(
            lambda media_resource: media_resource.total_size,
            self.store.media_resources_to_download,
        )
        total_download_size = sum(media_resource_sizes)
        formatted_download_size = self.formatter.format_data_size(total_download_size)

        is_preceded_by_format_warnings = (
            len(self.store.skipped_formats) > 0
            or len(self.store.formats_replaced_by_fallback) > 0
        )

        self.store.ready_to_download_label = screen.append_content(
            ("\n" if is_preceded_by_format_warnings else "")
            + "Ready to download "
            + colored(
                f"{formatted_title} ", fore=Colors.fore.CYAN, style=Colors.style.BRIGHT
            )
            + colored(
                f"{formatted_download_formats}\n",
                fore=Colors.fore.BLUE,
                style=Colors.style.BRIGHT,
            ),
            ContentCategories.INFO,
        )
        self.store.total_download_size_label = screen.append_content(
            "Total download size: "
            + colored(f"{formatted_download_size}\n", fore=Colors.fore.YELLOW),
            ContentCategories.INFO,
        )

    def ask_for_confirmation_to_download(self):
        prompt_message = self.formatter.format_download_confirmation_prompt_message()

        answer, prompt = screen.prompt(prompt_message, valid_inputs=["", "y", "n"])
        self.store.download_confirmation_prompt = prompt

        return answer != "n"

    def download_selected_formats(self):
        for media_resource in self.store.media_resources_to_download:
            self._create_download_progress(media_resource)

            screen_thread = Thread(target=self._keep_download_progress_ui_updated)
            screen_thread.start()

            media_resource.download()

            self.end_download_progress()

    def handle_download_progress(self, _stream, _chunk, bytes_remaining):
        downloading_stream = self.store.downloading_media_resource.downloading_stream

        if self.store.downloading_media_resource.output_type == "videoaudio":
            if downloading_stream is self.store.downloading_media_resource.video:
                self.store.downloading_media_resource.video_bytes_remaining = (
                    bytes_remaining
                )
            elif downloading_stream is self.store.downloading_media_resource.audio:
                self.store.downloading_media_resource.audio_bytes_remaining = (
                    bytes_remaining
                )

        if self.store.downloading_media_resource.output_type == "videoonly":
            self.store.downloading_media_resource.video_bytes_remaining = (
                bytes_remaining
            )

        if self.store.downloading_media_resource.output_type == "audio":
            self.store.downloading_media_resource.audio_bytes_remaining = (
                bytes_remaining
            )

    def end_download_progress(self):
        self._update_download_progress_ui()

        self.store.downloading_media_resource = None
        self.formatter.downloading_media_resource = None
        self.store.download_progress_ui = None

    def show_success_message(self):
        screen.append_content(
            colored("\nSuccess! ", fore=Colors.fore.GREEN)
            + "Files saved at "
            + colored(
                f"{self.store.output_path}/\n\n",
                fore=Colors.fore.CYAN,
            )
        )

    def clear_detailed_download_info_from_screen(self):
        if self.store.download_confirmation_prompt:
            screen.erase_prompt_entry(self.store.download_confirmation_prompt)
            screen.remove_content(self.store.download_confirmation_prompt)
        screen.remove_content(self.store.total_download_size_label)
        screen.remove_content(self.store.ready_to_download_label)
        screen.remove_content(self.store.video_heading)

    def reset_state(self):
        self.store.reset()

    def terminate(self):
        self.store.is_terminated = True
        self.loading_label = None
        self.is_loading = False

    def were_all_formats_skipped(self):
        return (
            len(self.store.media_resources_to_download) == 0
            and len(self.store.skipped_formats) > 0
        )

    def _show_header(self, video_urls_to_download):
        screen.append_content(self.formatter.format_header())

        if global_config.batch_file:
            self._show_batch_file_info(video_urls_to_download)

    def _show_batch_file_info(self, valid_video_urls_in_batch_file):
        batch_filename = path.basename(global_config.batch_file)

        screen.append_content(
            self.formatter.format_batch_file_info_header(batch_filename),
            ContentCategories.INFO,
        )
        screen.append_content(
            self.formatter.format_batch_file_info_body(valid_video_urls_in_batch_file),
            ContentCategories.INFO,
        )

    def _get_media_resources_to_download(self, formats):
        if len(formats) == 0:
            default_media_resource = MediaResource(
                self.store.video,
                "videoaudio",
                output_path=self.store.output_path,
                filename=self.store.filename,
            )

            return [default_media_resource]

        media_resources_to_download = []
        resources_registered_to_download = set()

        lowecased_formats = [selected_format.lower() for selected_format in formats]
        grouped_formats = self._group_and_validate_formats(lowecased_formats)

        definitions_count = {}
        for group in grouped_formats:
            download_format = group["format"]
            current_count = definitions_count.get(download_format, 0)
            definitions_count[download_format] = current_count + 1

        for group in grouped_formats:
            download_format = group["format"]
            definition = group["definition"]

            should_append_format_to_filename = definitions_count[download_format] > 1

            available_definition = self._get_available_definition(
                download_format, definition
            )

            if available_definition is None:
                self.store.skipped_formats.append([download_format, definition])
                continue

            if available_definition != definition:
                self.store.formats_replaced_by_fallback.append(
                    {
                        "base": {"format": download_format, "definition": definition},
                        "fallback": {
                            "format": download_format,
                            "definition": available_definition,
                        },
                    }
                )

            if (
                download_format,
                available_definition,
            ) in resources_registered_to_download:
                continue

            if should_append_format_to_filename:
                filename_suffix = (
                    f" [{download_format}] " if download_format != "videoaudio" else ""
                ) + (
                    f" [{available_definition}]"
                    if available_definition != "max"
                    else ""
                )
            else:
                filename_suffix = ""

            media_resource = MediaResource(
                self.store.video,
                download_format,
                output_path=self.store.output_path,
                definition=available_definition,
                filename=self.store.filename,
                filename_suffix=filename_suffix,
            )

            media_resources_to_download.append(media_resource)
            resources_registered_to_download.add(
                (download_format, available_definition)
            )

        return media_resources_to_download

    def _group_and_validate_formats(self, formats):
        grouped_formats = []

        format_index = 0
        while format_index < len(formats):
            current_item = formats[format_index]
            next_item = (
                formats[format_index + 1] if format_index < len(formats) - 1 else None
            )

            is_current_item_a_format = current_item in DOWNLOAD_FORMATS
            is_current_item_a_definition = current_item in AVAILABLE_DEFINITIONS
            is_next_item_a_format = next_item in DOWNLOAD_FORMATS
            is_next_item_a_definition = next_item in AVAILABLE_DEFINITIONS

            if is_current_item_a_format:
                if is_next_item_a_definition:
                    grouped_formats.append(
                        {"format": current_item, "definition": next_item}
                    )
                    format_index += 1
                elif next_item is None or is_next_item_a_format:
                    grouped_formats.append(
                        {"format": current_item, "definition": "max"}
                    )
                else:
                    self.store.skipped_formats.append([current_item, next_item])
                    format_index += 1

            elif is_current_item_a_definition:
                grouped_formats.append(
                    {"format": "videoaudio", "definition": current_item}
                )

            else:
                self.store.skipped_formats.append([current_item])

            format_index += 1

        return grouped_formats

    def _get_available_definition(self, base_format, base_definition):
        if base_format.startswith("video"):
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

            possible_definition = VIDEO_DEFINITIONS_ALIASES.get(
                possible_definition, possible_definition
            )

            possible_definition = (
                VIDEO_DEFINITIONS[possible_definition]["next"]
                if base_format.startswith("video")
                else AUDIO_DEFINITIONS[possible_definition]["next"]
            )

        return None

    def _is_definition_available(self, base_format, definition):
        if base_format.startswith("video"):
            final_definition = VIDEO_DEFINITIONS_ALIASES.get(definition, definition)

            if final_definition == "max":
                video_streams = self.store.video.streams.filter(type="video")

                return len(video_streams) > 0

            video_streams_with_specified_resolution = self.store.video.streams.filter(
                type="video", resolution=final_definition
            )

            return len(video_streams_with_specified_resolution) > 0

        else:
            if definition == "max":
                audio_streams = self.store.video.streams.filter(type="audio")

                return len(audio_streams) > 0

            audio_streams_with_specified_resolution = self.store.video.streams.filter(
                type="audio", abr=definition
            )

            return len(audio_streams_with_specified_resolution) > 0

    def _create_download_progress(self, media_resource):
        self.store.downloading_media_resource = media_resource
        self.formatter.downloading_media_resource = media_resource
        self.store.download_progress_ui = screen.append_content(
            self.formatter.format_current_download_progress()
        )

    def _keep_download_progress_ui_updated(self):
        while self.store.downloading_media_resource and not self.store.is_terminated:
            self._update_download_progress_ui()
            self._update_progress_ui_interval_if_necessary()

            sleep(self.store.PROGRESS_UI_UPDATE_INTERVAL)

    def _update_download_progress_ui(self):
        screen.update_content(
            self.store.download_progress_ui,
            self.formatter.format_current_download_progress(),
        )

    def _update_progress_ui_interval_if_necessary(self):
        download_status = self.store.downloading_media_resource.download_status
        required_interval = self.store.UI_UPDATE_INTERVALS.get(
            download_status, self.store.DEFAULT_UI_UPDATE_INTERVAL
        )

        if self.store.PROGRESS_UI_UPDATE_INTERVAL != required_interval:
            self.store.PROGRESS_UI_UPDATE_INTERVAL = required_interval

    def _get_available_formats(self):
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

    def _show_skipped_formats_warning(self):
        screen.append_content(
            self.formatter.format_skipped_formats_warning(), ContentCategories.WARNING
        )

    def _show_fallback_replacement_summary(self):
        for summary in self.formatter.format_fallback_replacement_summary():
            screen.append_content(summary, ContentCategories.WARNING)
