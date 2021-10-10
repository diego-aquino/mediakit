from urllib import parse
import re


ANSI_ESCAPE_CODES_REGEX = r"\x1b\[[;\d]*[A-Za-z]"

VIDEO_ID_REGEX = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
YOUTUBE_URL_REGEX = r"^https:\/\/.*youtu"
PLAYLIST_URL_REGEX = r"^https:\/\/.*youtube\.com\/playlist"


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


def matches_a_youtube_url(string):
    return bool(match(YOUTUBE_URL_REGEX, string, 0))


def extract_video_id(video_url):
    return search(VIDEO_ID_REGEX, video_url, 1)


def contains_video_id(string):
    video_id = extract_video_id(string)
    return video_id is not None


def is_youtube_video_url(string):
    return matches_a_youtube_url(string) and contains_video_id(string)


def matches_a_playlist_url(string):
    return bool(match(PLAYLIST_URL_REGEX, string, 0))


def extract_playlist_id(url):
    parsed_url = parse.urlparse(url)
    parsed_query = parse.parse_qs(parsed_url.query)

    if "list" not in parsed_query:
        return None

    return parsed_query["list"][0]


def contains_playlist_id(string):
    playlist_id = extract_playlist_id(string)
    return playlist_id is not None


def is_youtube_playlist_url(string):
    return matches_a_playlist_url(string) and contains_playlist_id(string)
