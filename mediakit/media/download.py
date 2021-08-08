from os import path

from mediakit.info import temp_filename
from mediakit.media.convert import (
    merge_video_and_audio,
    convert_media,
    ConversionOptions
)
from mediakit.utils.files import get_safe_filename, remove_file, move_file
from mediakit.constants import VIDEO_DEFINITIONS_ALIASES


class DownloadStatusCodes():
    READY = 'READY'
    DOWNLOADING = 'DOWNLOADING'
    CONVERTING = 'CONVERTING'
    DONE = 'DONE'


class MediaResource:
    def __init__(
        self,
        source,
        output_type,
        output_path=None,
        definition='max',
        filename='',
        filename_suffix=''
    ):
        self.source = source
        self.output_type = output_type
        self.output_path = output_path

        final_definition = (
            VIDEO_DEFINITIONS_ALIASES.get(definition, definition)
            if output_type.startswith('video')
            else definition
        )
        is_alias_definition = definition != final_definition

        if filename:
            filename_without_extension, extension = filename.split('.')
            self.filename = get_safe_filename(
                f'{filename_without_extension}{filename_suffix}.{extension}'
            )
        else:
            self.filename = get_safe_filename(
                f'{source.title}{filename_suffix}'
                + ('.mp4' if self.output_type.startswith('video') else '.mp3')
            )

        if output_type.startswith('video'):
            self.video = self._get_video_stream(final_definition)
            self.total_size = self.video.filesize
            self.video_bytes_remaining = self.video.filesize

            if output_type == 'videoaudio':
                if self._is_audio_included():
                    self.has_external_audio = False
                else:
                    self._include_external_audio()
                    self.has_external_audio = True

        elif output_type == 'audio':
            self.audio = self._get_audio_stream(final_definition)
            self.total_size = self.audio.filesize
            self.audio_bytes_remaining = self.audio.filesize

        self.formatted_definition = (
            f'[{output_type} '
            if output_type != 'videoaudio'
            else '['
        )

        if definition == 'max':
            self.formatted_definition += (
                f'{self.video.resolution}]'
                if self.output_type.startswith('video')
                else f'{self.audio.abr}]'
            )
        elif is_alias_definition:
            self.formatted_definition += f'{definition}]'
        else:
            self.formatted_definition += f'{final_definition}]'

        self.download_status = DownloadStatusCodes.READY
        self.downloading_stream = None

    def download(self):
        self.download_status = DownloadStatusCodes.DOWNLOADING

        if self.output_type.startswith('video'):
            self.downloading_stream = self.video

            self.video.download(
                output_path=self.output_path,
                filename=f'{temp_filename}[video].webm',
                skip_existing=False
            )
        if (self.output_type == 'audio'
            or (self.output_type == 'videoaudio' and self.has_external_audio)):
            self.downloading_stream = self.audio

            self.audio.download(
                output_path=self.output_path,
                filename=f'{temp_filename}[audio].webm',
                skip_existing=False
            )

        self.download_status = DownloadStatusCodes.CONVERTING
        self._convert_dowloaded_resources()
        self.download_status = DownloadStatusCodes.DONE

    def get_total_bytes_remaining(self):
        if self.output_type == 'videoaudio':
            if self.has_external_audio:
                return self.video_bytes_remaining + self.audio_bytes_remaining

            return self.video_bytes_remaining

        if self.output_type == 'videoonly':
            return self.video_bytes_remaining

        if self.output_type == 'audio':
            return self.audio_bytes_remaining

    def _convert_dowloaded_resources(self):
        if self.output_type.startswith('video'):
            if self.output_type == 'videoaudio' and self.has_external_audio:
                self._merge_video_with_external_audio()
            else:
                self._convert_downloaded_video()
        else:
            self._convert_downloaded_audio()

    def _merge_video_with_external_audio(self):
        downloaded_video_extension = self.video.mime_type.split('/')[-1]
        downloaded_audio_extension = self.audio.mime_type.split('/')[-1]

        video_path = path.join(
            self.output_path,
            f'{temp_filename}[video].{downloaded_video_extension}'
        )
        audio_path = path.join(
            self.output_path,
            f'{temp_filename}[audio].{downloaded_audio_extension}'
        )
        output_file_path = path.join(
            self.output_path,
            self.filename
        )

        merge_video_and_audio(video_path, audio_path, output_file_path)

        remove_file(video_path)
        remove_file(audio_path)

    def _convert_downloaded_video(self):
        downloaded_video_extension = self.video.mime_type.split('/')[-1]
        downloaded_temp_filename = (
            f'{temp_filename}[video].{downloaded_video_extension}'
        )

        downloaded_temp_file_path = path.join(
            self.output_path,
            downloaded_temp_filename
        )
        output_file_path = path.join(self.output_path, self.filename)

        options = []
        if self.output_type == 'videoonly':
            options.append(ConversionOptions.NO_AUDIO)

        convert_media(
            downloaded_temp_file_path,
            output_file_path,
            'mp4',
            options=options
        )
        remove_file(downloaded_temp_file_path)

    def _convert_downloaded_audio(self):
        downloaded_audio_extension = self.audio.mime_type.split('/')[-1]
        downloaded_temp_filename = (
            f'{temp_filename}[audio].{downloaded_audio_extension}'
        )

        downloaded_temp_file_path = path.join(
            self.output_path,
            downloaded_temp_filename
        )
        output_file_path = path.join(self.output_path, self.filename)

        convert_media(downloaded_temp_file_path, output_file_path, 'mp3')
        remove_file(downloaded_temp_file_path)

    def _is_audio_included(self):
        return self.video.is_progressive

    def _get_video_stream(self, definition):
        if definition == 'max':
            video_stream = (
                self.source.streams
                    .filter(type='video')
                    .order_by('resolution')[-1]
            )
        else:
            video_stream = (
                self.source.streams
                    .filter(type='video', resolution=definition)[-1]
            )

        return video_stream

    def _get_audio_stream(self, definition):
        if definition == 'max':
            audio_stream = (self.source.streams
                .filter(type='audio')
                .order_by('abr')[-1]
            )
        else:
            audio_stream = (self.source.streams
                .filter(type='audio', abr=definition)[-1]
            )

        return audio_stream

    def _include_external_audio(self):
        self.audio = self._get_audio_stream('max')

        self.total_size += self.audio.filesize
        self.audio_bytes_remaining = self.audio.filesize
