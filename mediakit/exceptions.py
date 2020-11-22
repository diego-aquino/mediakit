from mediakit.streams.screen import screen, ContentCategories
from mediakit.streams.colors import colored, Colors


class MediaKitException(Exception):
    def show_message(self):
        screen.append_content(self.message, self.category)


class CommandUnavailable(MediaKitException):
    def __init__(self, command):
        self.message = (
            f"Command '{command}' is not available.\n\n"
        )
        self.category = ContentCategories.ERROR

        super().__init__(self.message)


class FFMPEGNotAvailable(MediaKitException):
    def __init__(self):
        self.message = (
            'FFmpeg is a required package for MediaKit, '
            "but it doesn't appear to be installed.\n"
            'You can install FFmpeg at https://ffmpeg.org/download.html.\n\n'
        )
        self.category = ContentCategories.WARNING

        super().__init__(self.message)


class InvalidVideoURLError(MediaKitException):
    def __init__(self):
        self.message = (
            'Could not recognize the provided URL. Please, try again.\n\n'
        )
        self.category = ContentCategories.ERROR

        super().__init__(self.message)


class UnspecifiedError(MediaKitException):
    def __init__(self):
        self.message = 'Something went wrong. :(\nPlease, try again.\n\n'
        self.category = ContentCategories.ERROR

        super().__init__(self.message)


class NoAvailableSpecifiedFormats(MediaKitException):
    def __init__(self, available_formats):
        self.message = (
            'None of the specified formats were found.\n'
            + 'Please, verify your entries and try again.\n\n'

            + 'The formats available for this video are: '
            + colored(
                ' '.join(available_formats),
                fore=Colors.fore.BLUE,
                style=Colors.style.BRIGHT
            )
            + '\n\n'
        )
        self.category = ContentCategories.ERROR

        super().__init__(self.message)
