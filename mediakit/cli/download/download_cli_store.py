from threading import Thread
from pytube import YouTube

from mediakit.cli.screen import Content, ContentCategories, screen
from mediakit.cli.loadble_cli_store import LoadableCLIStore
from mediakit.media.download import DownloadStatusCodes, MediaResource


class DownloadCLIStore(LoadableCLIStore):
    def __init__(self):
        self.MAX_SCREEN_WIDTH = 80
        self.MAX_SHORT_VIDEO_TITLE_LENGTH = 26

        self.UI_UPDATE_INTERVALS = {
            DownloadStatusCodes.DOWNLOADING: 0.15,
            DownloadStatusCodes.CONVERTING: 0.1,
        }
        self.DEFAULT_UI_UPDATE_INTERVAL = 0.2
        self.PROGRESS_UI_UPDATE_INTERVAL = self.DEFAULT_UI_UPDATE_INTERVAL

        self.video_headings: "list[Content]" = []
        self.ready_to_download_labels: "list[Content]" = []
        self.download_confirmation_prompts: "list[Content]" = []

        self.output_path: str = None
        self.filename: str = None

        self.videos: "list[YouTube]" = []

        self.available_formats = []
        self.media_resources_to_download: "list[MediaResource]" = []
        self.skipped_formats = []
        self.formats_replaced_by_fallback = []

        self.downloading_media_resources: "list[MediaResource]" = []
        self.download_progress_uis: "list[Content]" = []
        self.rotating_line_frames: "list[int]" = []
        self.loading_dots_frames: "list[int]" = []

        self.download_ui_update_thread: Thread = None

        self.is_terminated: bool = False

    def prepare_store(self, number_of_videos: int):
        self.videos = [None for _ in range(number_of_videos)]
        self.available_formats = [
            {"video": [], "audio": []} for _ in range(number_of_videos)
        ]
        self.media_resources_to_download = [None for _ in range(number_of_videos)]
        self.skipped_formats = [[] for _ in range(number_of_videos)]
        self.formats_replaced_by_fallback = [[] for _ in range(number_of_videos)]

        self.downloading_media_resources = [None for _ in range(number_of_videos)]

        self.video_headings = [None for _ in range(number_of_videos)]
        self.ready_to_download_labels = [None for _ in range(number_of_videos)]
        self.download_progress_uis = [None for _ in range(number_of_videos)]
        self.download_confirmation_prompts: "list[Content]" = [
            None for _ in range(number_of_videos)
        ]

        self.rotating_line_frames = [0 for _ in range(number_of_videos)]
        self.loading_dots_frames = [0 for _ in range(number_of_videos)]

    def reset(self):
        super().reset()

        self.video_headings: "list[Content]" = []
        self.ready_to_download_labels: "list[Content]" = []
        self.download_confirmation_prompts: "list[Content]" = []

        self.output_path: str = None
        self.filename: str = None

        self.videos: "list[YouTube]" = []

        self.available_formats = []
        self.media_resources_to_download: "list[MediaResource]" = []
        self.skipped_formats = []
        self.formats_replaced_by_fallback = []

        self.downloading_media_resources: "list[MediaResource]" = []
        self.download_progress_uis: "list[Content]" = []
        self.rotating_line_frames: "list[int]" = []
        self.loading_dots_frames: "list[int]" = []
