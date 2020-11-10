from os import path

from mediakit.info import temp_filename
from mediakit.media.merge import merge_video_and_audio
from mediakit.utils.files import remove_file
from . import statuscodes


class MediaResource:
    def __init__(
        self,
        source,
        output_type,
        output_path=None,
        definition='max',
        filename=''
    ):
        self.source = source
        self.output_type = output_type
        self.output_path = output_path

        self.filename = (
            filename if filename
            else f'{source.title}.mp4'
        )

        if output_type == 'video/audio':
            self.video = self._get_video_stream(definition)
            self.total_size = self.video.filesize
            self.video_bytes_remaining = self.video.filesize

            if self._is_audio_included():
                self.has_external_audio = False
            else:
                self._include_external_audio()
                self.has_external_audio = True

        elif output_type == 'video-only':
            self.video = self._get_video_stream(definition)
            self.total_size = self.video.filesize
            self.video_bytes_remaining = self.video.filesize

        elif output_type == 'audio-only':
            self.audio = self._get_audio_stream(definition)
            self.total_size = self.audio.filesize
            self.audio_bytes_remaining = self.audio.filesize

        self.formatted_definition = (
            f'[{self.video.resolution}]' if self.output_type.startswith('video')
            else f'[{self.audio.abr}]'
        )

        self.download_status = statuscodes.ready

    def download(self):
        self.download_status = statuscodes.downloading

        if self.output_type.startswith('video'):
            self.downloading_stream = self.video

            self.video.download(
                output_path=self.output_path,
                filename=temp_filename,
                skip_existing=False
            )
        if (self.output_type == 'audio-only'
            or (self.output_type == 'video/audio' and self.has_external_audio)):
            self.downloading_stream = self.audio

            self.audio.download(
                output_path=self.output_path,
                filename=temp_filename,
                skip_existing=False
            )

        if self.output_type == 'video/audio' and self.has_external_audio:
            self.download_status = statuscodes.converting
            self._merge_video_with_external_audio()

        self.download_status = statuscodes.done

    def get_total_bytes_remaining(self):
        if self.output_type == 'video/audio':
            if self.has_external_audio:
                return self.video_bytes_remaining + self.audio_bytes_remaining

            return self.video_bytes_remaining

        elif self.output_type == 'video-only':
            return self.video_bytes_remaining

        elif self.output_type == 'audio-only':
            return self.audio_bytes_remaining

    def _merge_video_with_external_audio(self):
        downloaded_video_extension = self.video.mime_type.split('/')[-1]
        downloaded_audio_extension = self.audio.mime_type.split('/')[-1]

        video_path = path.join(
            self.output_path,
            f'{temp_filename}.{downloaded_video_extension}'
        )
        audio_path = path.join(
            self.output_path,
            f'{temp_filename}.{downloaded_audio_extension}'
        )
        output_file_path = path.join(
            self.output_path,
            self.filename
        )

        merge_video_and_audio(video_path, audio_path, output_file_path)

        remove_file(video_path)
        remove_file(audio_path)

    def _is_audio_included(self):
        return self.video.is_progressive

    def _get_video_stream(self, definition):
        if definition == 'max':
            video_stream = (
                self.source.streams
                    .filter(mime_type='video/mp4')
                    .order_by('resolution')[-1]
            )
        else:
            video_stream = (
                self.source.streams
                    .filter(mime_type='video/mp4', resolution=definition)[-1]
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
