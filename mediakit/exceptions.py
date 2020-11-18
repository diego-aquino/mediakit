from mediakit.streams.screen import screen, ContentCategories


class MediaKitException(Exception):
    pass


class CommandUnavailable(MediaKitException):
    def __init__(self, command):
        self.message = (
            f"Command '{command}' is not available.\n"
        )
        self.category = ContentCategories.ERROR

        super().__init__(self.message)


class FFMPEGNotAvailable(MediaKitException):
    def __init__(self):
        self.message = (
            'FFmpeg is a required package for MediaKit, '
            "but it doesn't appear to be installed.\n"
            'You can install FFmpeg at https://ffmpeg.org/download.html.\n'
        )
        self.category = ContentCategories.WARNING

        super().__init__(self.message)


class InvalidVideoURLError(MediaKitException):
    def __init__(self):
        self.message = (
            'Could not recognize the provided URL. Please, try again.\n'
        )
        self.category = ContentCategories.ERROR

        super().__init__(self.message)


class UnspecifiedError(MediaKitException):
    def __init__(self):
        self.message = 'Something went wrong. :(\nPlease, try again.\n'
        self.category = ContentCategories.ERROR

        super().__init__(self.message)


def show_exception_message(exception):
    screen.append_content(exception.message, exception.category)
