from os import path
from functools import partial
from threading import Thread
from time import sleep
from typing import Callable
from pytube import YouTube

from mediakit.cli.screen import Content, screen, ContentCategories
from mediakit.cli.colors import colored, Colors
from mediakit.media.download import DownloadStatusCodes, MediaResource
from mediakit.utils.format import limit_text_length, parse_int
from mediakit.cli.loadble_cli import LoadableCLI
from mediakit.cli.download.download_cli_formatter import DownloadCLIFormatter
from mediakit.cli.download.download_cli_store import DownloadCLIStore
from mediakit.constants import (
    DOWNLOAD_FORMATS,
    FFMPEG_BINARY,
    VIDEO_DEFINITIONS,
    VIDEO_DEFINITIONS_ALIASES,
    AUDIO_DEFINITIONS,
    AVAILABLE_DEFINITIONS,
)
from mediakit.globals import global_config
from mediakit import exceptions


class DownloadCLI(LoadableCLI):
    def __init__(self, output_path: str, filename: str):
        self.store = DownloadCLIStore()
        self.store.filename = filename
        self.store.output_path = output_path

        self.formatter = DownloadCLIFormatter(self.store)

    def start(self, video_urls_to_download: "list[str]", formats):
        self._show_header(video_urls_to_download)

        if not FFMPEG_BINARY:
            exceptions.FFMPEGNotAvailable().show_message()
            return

        self.mark_as_loading(True, len(video_urls_to_download))
        self._register_videos_to_download(video_urls_to_download, formats)
        self.mark_as_loading(False)

    def mark_as_loading(self, is_loading: bool, number_of_videos_being_loaded=1):
        self.store.is_loading = is_loading

        if is_loading:
            loading_label = (
                "Loading videos (this might take a while)"
                if number_of_videos_being_loaded > 1
                else "Loading video"
            )
            self._show_loading_label(loading_label)
        else:
            self._remove_loading_label()

    def _show_header(self, video_urls_to_download):
        screen.append_content(self.formatter.format_header())

        if global_config.batch_file:
            self._show_batch_file_info(video_urls_to_download)

    def _register_videos_to_download(self, video_urls: str, formats: "list[str]"):
        self.store.prepare_store(len(video_urls))

        for video_index in range(len(video_urls)):
            video = YouTube(video_urls[video_index])
            self.store.videos[video_index] = video

            def handle_download_progress(video_index, _stream, _chunk, bytes_remaining):
                self._handle_download_progress(video_index, bytes_remaining)

            video.register_on_progress_callback(
                partial(handle_download_progress, video_index)
            )

            available_formats = self._get_available_formats(video_index)
            self.store.available_formats[video_index] = available_formats

            media_resources = self._get_media_resources_to_download(
                video_index, formats
            )
            self.store.media_resources_to_download[video_index] = media_resources

    def _get_available_formats(self, video_index: int):
        video_streams = self.store.videos[video_index].streams.filter(type="video")
        audio_streams = self.store.videos[video_index].streams.filter(type="audio")

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

    def download_all(self):
        self._prerender_download_ui_components()

        at_least_one_file_was_downloaded = False

        self.store.download_ui_update_thread = Thread(
            target=self._keep_download_progress_ui_updated
        )
        self.store.download_ui_update_thread.start()

        video_indexes_left_to_download = list(range(len(self.store.videos) - 1, -1, -1))
        ongoing_download_threads: "list[Thread]" = []

        def download(video_index: int, on_finish: Callable[..., None]):
            nonlocal at_least_one_file_was_downloaded

            for media_resource in self.store.media_resources_to_download[video_index]:
                self._create_download_progress(video_index, media_resource)

                media_resource.download()

                self._end_download_progress(video_index)
                at_least_one_file_was_downloaded = True

                on_finish()

        def start_next_download():
            if len(video_indexes_left_to_download) == 0:
                return

            video_index = video_indexes_left_to_download.pop()

            self._show_download_summary(video_index)

            should_ask_confirmation_to_download = (
                not global_config.answer_yes_to_all_questions
                and global_config.batch_file is None
            )
            if should_ask_confirmation_to_download:
                user_has_confirmed = self._ask_for_confirmation_to_download(video_index)
                if not user_has_confirmed:
                    return

            download_thread = Thread(
                target=partial(download, video_index, start_next_download)
            )
            ongoing_download_threads.append(download_thread)
            download_thread.start()

        number_of_starter_videos = min(
            global_config.max_downloads_in_parallel,
            len(video_indexes_left_to_download),
        )

        for _ in range(number_of_starter_videos):
            start_next_download()

        for thread in ongoing_download_threads:
            thread.join()

        if at_least_one_file_was_downloaded:
            self._show_success_message()

    def _show_download_summary(self, video_index: int):
        screen.update_content(
            self.store.video_headings[video_index],
            self.formatter.format_download_summary(video_index),
        )

        if self._were_all_formats_skipped(video_index):
            raise exceptions.NoAvailableSpecifiedFormats(
                self.store.available_formats[video_index]
            )

        if global_config.batch_file is None:
            screen.update_content(
                self.store.ready_to_download_labels[video_index],
                self.formatter.format_ready_to_download_label(video_index),
            )

    def _ask_for_confirmation_to_download(self, video_index: int):
        prompt = self.store.download_confirmation_prompts[video_index]

        prompt_message = self.formatter.format_download_confirmation_prompt_message()
        answer = screen.prompt(
            prompt_message,
            valid_inputs=["", "y", "n"],
            index_on_screen=prompt.index_on_screen,
        )

        return answer != "n"

    def _create_download_progress(
        self, video_index: int, media_resource: MediaResource
    ):
        self.store.downloading_media_resources[video_index] = media_resource
        screen.update_content(
            self.store.download_progress_uis[video_index],
            self.formatter.format_current_download_progress(video_index),
        )

    def _prerender_download_ui_components(self):
        for video_index in range(len(self.store.videos)):
            self.store.video_headings[video_index] = screen.append_content("")
            self.store.ready_to_download_labels[video_index] = screen.append_content("")
            self.store.download_confirmation_prompts[
                video_index
            ] = screen.append_content("")
            self.store.download_progress_uis[video_index] = screen.append_content("")

    def _keep_download_progress_ui_updated(self):
        has_detailed_download_info_on_screen = [True for _ in self.store.videos]

        while not self.store.is_terminated:
            self._update_all_download_progress_uis(has_detailed_download_info_on_screen)
            sleep(self.store.PROGRESS_UI_UPDATE_INTERVAL)

    def _update_all_download_progress_uis(
        self, has_detailed_download_info_on_screen: "list[bool]"
    ):
        for video_index in range(len(self.store.videos)):
            media_resources = self.store.media_resources_to_download[video_index]

            all_media_resources_are_done = all(
                map(
                    lambda media_resource: media_resource.download_status
                    == DownloadStatusCodes.DONE,
                    media_resources,
                )
            )

            should_clear_detailed_download_info = (
                all_media_resources_are_done
                and has_detailed_download_info_on_screen[video_index]
            )

            if should_clear_detailed_download_info:
                self._clear_detailed_download_info_from_screen(video_index)
                has_detailed_download_info_on_screen[video_index] = False

        videos_with_downloading_media_resources = [
            video_index
            for video_index in range(len(self.store.videos))
            if self.store.downloading_media_resources[video_index] is not None
        ]

        for video_index in videos_with_downloading_media_resources:
            self._update_download_progress_ui(video_index)
            self._update_progress_ui_interval_if_necessary(video_index)

    def _update_download_progress_ui(self, video_index: int):
        screen.update_content(
            self.store.download_progress_uis[video_index],
            self.formatter.format_current_download_progress(video_index),
        )

    def _update_progress_ui_interval_if_necessary(self, video_index: int):
        media_resource = self.store.downloading_media_resources[video_index]
        required_interval = self.store.UI_UPDATE_INTERVALS.get(
            media_resource.download_status, self.store.DEFAULT_UI_UPDATE_INTERVAL
        )

        if self.store.PROGRESS_UI_UPDATE_INTERVAL != required_interval:
            self.store.PROGRESS_UI_UPDATE_INTERVAL = required_interval

    def _handle_download_progress(self, video_index: int, bytes_remaining: int):
        media_resource = self.store.downloading_media_resources[video_index]
        downloading_stream = media_resource.downloading_stream

        if media_resource.output_type == "videoaudio":
            if downloading_stream is media_resource.video:
                media_resource.video_bytes_remaining = bytes_remaining
            elif downloading_stream is media_resource.audio:
                media_resource.audio_bytes_remaining = bytes_remaining

        if media_resource.output_type == "videoonly":
            media_resource.video_bytes_remaining = bytes_remaining

        if media_resource.output_type == "audio":
            media_resource.audio_bytes_remaining = bytes_remaining

    def _end_download_progress(self, video_index: int):
        self._update_download_progress_ui(video_index)

        self.store.downloading_media_resources[video_index] = None
        self.store.download_progress_uis[video_index] = None

    def _show_success_message(self):
        screen.append_content(
            colored("\nSuccess! ", fore=Colors.fore.GREEN)
            + "Files saved at "
            + colored(
                f"{self.store.output_path}/\n\n",
                fore=Colors.fore.CYAN,
            )
        )

    def _clear_detailed_download_info_from_screen(self, video_index: int):
        video_heading = self.store.video_headings[video_index]
        ready_to_download_label = self.store.ready_to_download_labels[video_index]
        confirmation_prompt = self.store.download_confirmation_prompts[video_index]

        screen.update_content(video_heading, "")
        screen.update_content(ready_to_download_label, "")

        if not confirmation_prompt.is_empty():
            screen.erase_prompt_entry(confirmation_prompt)
            screen.update_content(confirmation_prompt, "")

    def terminate(self):
        self._update_all_download_progress_uis([True for _ in self.store.videos])

        self.store.loading_label = None
        self.store.is_loading = False

        self.store.is_terminated = True

        if self.store.download_ui_update_thread is not None:
            self.store.download_ui_update_thread.join()

    def _were_all_formats_skipped(self, video_index: int):
        return (
            len(self.store.media_resources_to_download[video_index]) == 0
            and len(self.store.skipped_formats[video_index]) > 0
        )

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

    def _get_media_resources_to_download(self, video_index: int, formats):
        if len(formats) == 0:
            default_media_resource = MediaResource(
                self.store.videos[video_index],
                "videoaudio",
                output_path=self.store.output_path,
                filename=self.store.filename,
            )

            return [default_media_resource]

        media_resources_to_download = []
        resources_registered_to_download = set()

        lowecased_formats = [selected_format.lower() for selected_format in formats]
        grouped_formats = self._group_and_validate_formats(
            video_index, lowecased_formats
        )

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
                video_index, download_format, definition
            )

            if available_definition is None:
                self.store.skipped_formats[video_index].append(
                    [download_format, definition]
                )
                continue

            if available_definition != definition:
                self.store.formats_replaced_by_fallback[video_index].append(
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
                self.store.videos[video_index],
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

    def _group_and_validate_formats(self, video_index: int, formats):
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
                    self.store.skipped_formats[video_index].append(
                        [current_item, next_item]
                    )
                    format_index += 1

            elif is_current_item_a_definition:
                grouped_formats.append(
                    {"format": "videoaudio", "definition": current_item}
                )

            else:
                self.store.skipped_formats[video_index].append([current_item])

            format_index += 1

        return grouped_formats

    def _get_available_definition(self, video_index, base_format, base_definition):
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
            if self._is_definition_available(
                video_index, base_format, possible_definition
            ):
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

    def _is_definition_available(
        self, video_index: int, base_format: str, definition: str
    ):
        video = self.store.videos[video_index]

        if base_format.startswith("video"):
            final_definition = VIDEO_DEFINITIONS_ALIASES.get(definition, definition)

            if final_definition == "max":
                video_streams = self.store.videos[video_index].streams.filter(
                    type="video"
                )
                return len(video_streams) > 0

            video_streams_with_specified_resolution = video.streams.filter(
                type="video", resolution=final_definition
            )
            return len(video_streams_with_specified_resolution) > 0

        else:
            if definition == "max":
                audio_streams = video.streams.filter(type="audio")
                return len(audio_streams) > 0

            audio_streams_with_specified_resolution = video.streams.filter(
                type="audio", abr=definition
            )
            return len(audio_streams_with_specified_resolution) > 0
