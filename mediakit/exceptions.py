class MediaKitError(Exception):
    pass


class CommandUnavailable(MediaKitError):
    def __init__(self, command):
        if command == 'ffmpeg':
            self.message = (
                'warning - FFmpeg is a required package for MediaKit, '
                "but it doesn't appear to be installed.\n"
                'You can install FFmpeg at https://ffmpeg.org/download.html.'
            )
        else:
            self.message = (
                f"error - Command '{command}' is not available."
            )

        super().__init__(self.message)


class InvalidVideoURLError(MediaKitError):
    def __init__(self):
        self.message = (
            'error - Could not recognize the provided URL. Please, try again.'
        )

        super().__init__(self.message)


class UnspecifiedError(MediaKitError):
    def __init__(self):
        self.message = (
            'error - Something went wrong. :(\n'
            'Please, try again.'
        )

        super().__init__(self.message)
