import re


ANSI_ESCAPE_CODES_REGEX = r'\x1b\[[;\d]*[A-Za-z]'

VIDEO_ID_REGEX = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
YOUTUBE_URL_REGEX = r'https:\/\/.*youtu'


def search(pattern, string, group):
    regex = re.compile(pattern)
    results = regex.search(string)

    if not results:
        return None

    return results.group(group)


def match(pattern, string, group):
    regex = re.compile(pattern)
    results = regex.match(string)

    if not results:
        return None

    return results.group(group)


def sub(pattern, replacement, string):
    regex = re.compile(pattern)
    replaced_string = regex.sub(replacement, string)

    return replaced_string


def extract_video_id(video_url):
    return search(VIDEO_ID_REGEX, video_url, 1)


def matches_a_youtube_url(string):
    return match(YOUTUBE_URL_REGEX, string, 0)


def is_video_url_like(string):
    video_id = extract_video_id(string)
    if video_id is not None or matches_a_youtube_url(string):
        return True

    return False
