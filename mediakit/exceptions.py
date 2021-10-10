import sys
from mediakit.cli.screen import Content, ContentCategories
from mediakit.cli.colors import colored, Colors


class MediakitException(Exception):
    def __init__(self, message, category):
        self.message = message
        self.category = category

    def show_message(self):
        print(Content.format_inner_text(self.message, self.category), file=sys.stderr)


class CommandUnavailable(MediakitException):
    def __init__(self, command):
        message = f"Command '{command}' is not available.\n\n"
        category = ContentCategories.ERROR

        super().__init__(message, category)


class FFMPEGNotAvailable(MediakitException):
    def __init__(self):
        message = (
            "FFmpeg is a required package for Mediakit, "
            "but it doesn't appear to be installed.\n"
            "You can install FFmpeg at https://ffmpeg.org/download.html.\n\n"
        )
        category = ContentCategories.WARNING

        super().__init__(message, category)


class InvalidVideoURLError(MediakitException):
    def __init__(self):
        message = "Could not recognize the provided video URL. Please, try again.\n\n"
        category = ContentCategories.ERROR

        super().__init__(message, category)


class InvalidPlaylistURLError(MediakitException):
    def __init__(self):
        message = (
            "Could not recognize the provided playlist URL. Please, try again.\n\n"
        )
        category = ContentCategories.ERROR

        super().__init__(message, category)


class UnspecifiedError(MediakitException):
    def __init__(self):
        message = "Something went wrong. :(\nPlease, try again.\n\n"
        category = ContentCategories.ERROR

        super().__init__(message, category)


class NoAvailableSpecifiedFormats(MediakitException):
    def __init__(self, available_formats):
        message = (
            "None of the specified formats were found.\n"
            + "Please, verify your entries and try again.\n\n"
            + "The formats available for this video are:\n"
            + colored("   (video) ", style=Colors.style.DIM + Colors.style.BRIGHT)
            + colored(
                " ".join(available_formats["video"]),
                fore=Colors.fore.BLUE,
                style=Colors.style.BRIGHT,
            )
            + colored("\n   (audio) ", style=Colors.style.DIM + Colors.style.BRIGHT)
            + colored(
                " ".join(available_formats["audio"]),
                fore=Colors.fore.BLUE,
                style=Colors.style.BRIGHT,
            )
            + "\n\n"
        )
        category = ContentCategories.ERROR

        super().__init__(message, category)


class NoSuchFile(MediakitException):
    def __init__(self, supposed_file):
        message = (
            "\nNo such file: "
            + colored(supposed_file, fore=Colors.fore.MAGENTA)
            + "\n\n"
        )
        category = ContentCategories.ERROR

        super().__init__(message, category)


class NoVideoURLsInBatchFile(MediakitException):
    def __init__(self, batch_file):
        message = (
            "\nCould not find any valid video URLs in "
            + colored(batch_file, fore=Colors.fore.MAGENTA)
            + "\nPlease check your entries and try again.\n\n"
        )
        category = ContentCategories.ERROR

        super().__init__(message, category)


class EmptyPlaylistException(MediakitException):
    def __init__(self):
        message = (
            "\nCould not find any videos in this playlist.\n"
            + "Make sure it exists and is marked as public.\n\n"
        )
        category = ContentCategories.ERROR

        super().__init__(message, category)
