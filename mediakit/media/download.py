from os import path
import uuid

from pytube.__main__ import YouTube

from mediakit import info
from mediakit.media.convert import (
    merge_video_and_audio,
    convert_media,
    ConversionOptions,
)
from mediakit.utils.files import get_safe_filename, remove_file, move_file
from mediakit.constants import VIDEO_DEFINITIONS_ALIASES


class DownloadStatusCodes:
    READY = "READY"
    DOWNLOADING = "DOWNLOADING"
    CONVERTING = "CONVERTING"
    DONE = "DONE"


class MediaResource:
    def __init__(
        self,
        source,
        output_type,
        output_path=None,
        definition="max",
        filename="",
        filename_suffix="",
    ):
        self.source = source
        self.output_type = output_type
        self.output_path = output_path
        self.definition = definition

        final_definition = (
            VIDEO_DEFINITIONS_ALIASES.get(definition, definition)
            if output_type.startswith("video")
            else definition
        )
        is_alias_definition = definition != final_definition

        default_extension = "mp4" if self.output_type.startswith("video") else "mp3"

        if filename:
            *initial_filename_components, last_filename_component = filename.split(".")

            extension_was_provided = len(initial_filename_components) > 0

            if extension_was_provided:
                filename_without_extension = (
                    ".".join(initial_filename_components) + filename_suffix
                )
                extension = last_filename_component
                self.filename = get_safe_filename(
                    f"{filename_without_extension}.{extension}"
                )
            else:
                filename_without_extension = last_filename_component + filename_suffix
                self.filename = get_safe_filename(
                    f"{filename_without_extension}.{default_extension}"
                )
        else:
            filename_without_extension = source.title + filename_suffix
            self.filename = get_safe_filename(
                f"{filename_without_extension}.{default_extension}"
            )

        if output_type.startswith("video"):
            self.video = self._get_video_stream(final_definition)
            self.total_size = self.video.filesize
            self.video_bytes_remaining = self.video.filesize

            if output_type == "videoaudio":
                if self._is_audio_included():
                    self.has_external_audio = False
                else:
                    self._include_external_audio()
                    self.has_external_audio = True

        elif output_type == "audio":
            self.audio = self._get_audio_stream(final_definition)
            self.total_size = self.audio.filesize
            self.audio_bytes_remaining = self.audio.filesize

        self.formatted_definition = (
            f"[{output_type} " if output_type != "videoaudio" else "["
        )

        if definition == "max":
            self.formatted_definition += (
                f"{self.video.resolution}]"
                if self.output_type.startswith("video")
                else f"{self.audio.abr}]"
            )
        elif is_alias_definition:
            self.formatted_definition += f"{definition}]"
        else:
            self.formatted_definition += f"{final_definition}]"

        self.download_status = DownloadStatusCodes.READY
        self.downloading_stream = None

        unique_resource_id = uuid.uuid4()
        self.temporary_video_filename = (
            f"{info.temporary_filename}-{unique_resource_id}[video].webm"
        )
        self.temporary_audio_filename = (
            f"{info.temporary_filename}-{unique_resource_id}[audio].webm"
        )

    def download(self):
        self.download_status = DownloadStatusCodes.DOWNLOADING

        if self.output_type.startswith("video"):
            self.downloading_stream = self.video

            self.video.download(
                output_path=self.output_path,
                filename=self.temporary_video_filename,
                skip_existing=False,
            )
        if self.output_type == "audio" or (
            self.output_type == "videoaudio" and self.has_external_audio
        ):
            self.downloading_stream = self.audio

            self.audio.download(
                output_path=self.output_path,
                filename=self.temporary_audio_filename,
                skip_existing=False,
            )

        self.download_status = DownloadStatusCodes.CONVERTING
        self._convert_dowloaded_resources()
        self.download_status = DownloadStatusCodes.DONE

    def get_total_bytes_remaining(self):
        if self.output_type == "videoaudio":
            if self.has_external_audio:
                return self.video_bytes_remaining + self.audio_bytes_remaining

            return self.video_bytes_remaining

        if self.output_type == "videoonly":
            return self.video_bytes_remaining

        if self.output_type == "audio":
            return self.audio_bytes_remaining

    def copy(self, source: YouTube = None):
        final_source = source if source is not None else self.source

        return MediaResource(
            final_source,
            self.output_type,
            output_path=self.output_path,
            definition=self.definition,
            filename=self.filename,
        )

    def _convert_dowloaded_resources(self):
        if self.output_type.startswith("video"):
            if self.output_type == "videoaudio" and self.has_external_audio:
                self._merge_video_with_external_audio()
            else:
                self._convert_downloaded_video()
        else:
            self._convert_downloaded_audio()

    def _merge_video_with_external_audio(self):
        video_path = path.join(self.output_path, self.temporary_video_filename)
        audio_path = path.join(self.output_path, self.temporary_audio_filename)
        output_file_path = path.join(self.output_path, self.filename)

        merge_video_and_audio(video_path, audio_path, output_file_path)

        remove_file(video_path)
        remove_file(audio_path)

    def _convert_downloaded_video(self):
        downloaded_temp_file_path = path.join(
            self.output_path, self.temporary_video_filename
        )
        output_file_path = path.join(self.output_path, self.filename)

        options = []
        if self.output_type == "videoonly":
            options.append(ConversionOptions.NO_AUDIO)

        convert_media(
            downloaded_temp_file_path, output_file_path, "mp4", options=options
        )
        remove_file(downloaded_temp_file_path)

    def _convert_downloaded_audio(self):
        downloaded_temp_filename = self.temporary_audio_filename

        downloaded_temp_file_path = path.join(
            self.output_path, downloaded_temp_filename
        )
        output_file_path = path.join(self.output_path, self.filename)

        convert_media(downloaded_temp_file_path, output_file_path, "mp3")
        remove_file(downloaded_temp_file_path)

    def _is_audio_included(self):
        return self.video.is_progressive

    def _get_video_stream(self, definition):
        if definition == "max":
            video_stream = self.source.streams.filter(type="video").order_by(
                "resolution"
            )[-1]
        else:
            video_stream = self.source.streams.filter(
                type="video", resolution=definition
            )[-1]

        return video_stream

    def _get_audio_stream(self, definition):
        if definition == "max":
            audio_stream = self.source.streams.filter(type="audio").order_by("abr")[-1]
        else:
            audio_stream = self.source.streams.filter(type="audio", abr=definition)[-1]

        return audio_stream

    def _include_external_audio(self):
        self.audio = self._get_audio_stream("max")

        self.total_size += self.audio.filesize
        self.audio_bytes_remaining = self.audio.filesize
