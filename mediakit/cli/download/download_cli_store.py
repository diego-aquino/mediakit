from pytube import YouTube

from mediakit.cli.screen import Content
from mediakit.cli.loadble_cli_store import LoadableCLIStore
from mediakit.media.download import DownloadStatusCodes, MediaResource


class DownloadCLIStore(LoadableCLIStore):
    def __init__(self):
        self.UI_UPDATE_INTERVALS = {
            DownloadStatusCodes.DOWNLOADING: 0.2,
            DownloadStatusCodes.CONVERTING: 0.1,
        }
        self.DEFAULT_UI_UPDATE_INTERVAL = 0.2
        self.PROGRESS_UI_UPDATE_INTERVAL = self.DEFAULT_UI_UPDATE_INTERVAL

        self.MAX_SCREEN_WIDTH = 80
        self.MAX_SHORT_VIDEO_TITLE_LENGTH = 26

        self.video_heading: Content = None
        self.ready_to_download_label: Content = None
        self.total_download_size_label: Content = None
        self.download_confirmation_prompt: Content = None

        self.video: YouTube = None
        self.output_path: str = None
        self.filename: str = None
        self.short_video_title: str = None

        self.available_formats = {"video": [], "audio": []}
        self.media_resources_to_download = []
        self.skipped_formats = []
        self.formats_replaced_by_fallback = []

        self.downloading_media_resource: MediaResource = None
        self.download_progress_ui: Content = None
        self.rotating_line_frame: int = 0
        self.loading_dots_frame: int = 0

        self.is_terminated: bool = False

    def reset(self):
        super().reset()

        self.video_heading: Content = None
        self.ready_to_download_label: Content = None
        self.total_download_size_label: Content = None
        self.download_confirmation_prompt: Content = None

        self.video: YouTube = None
        self.output_path: str = None
        self.filename: str = None
        self.short_video_title: str = None

        self.available_formats = {"video": [], "audio": []}
        self.media_resources_to_download = []
        self.skipped_formats = []
        self.formats_replaced_by_fallback = []

        self.downloading_media_resource: MediaResource = None
        self.download_progress_ui: Content = None
        self.rotating_line_frame: int = 0
        self.loading_dots_frame: int = 0

        self.is_terminated: bool = False
