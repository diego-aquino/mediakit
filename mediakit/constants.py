from .utils.ffmpeg import get_ffmpeg_binary


FFMPEG_BINARY = get_ffmpeg_binary()

DOWNLOAD_FORMATS = { 'videoaudio', 'audio', 'videoonly' }

VIDEO_DEFINITIONS = {
    'max': { 'next': '2160p' },
    '2160p': { 'next': '1440p' },
    '1440p': { 'next': '1080p' },
    '1080p': { 'next': '720p' },
    '720p': { 'next': '480p' },
    '480p': { 'next': '360p' },
    '360p': { 'next': '240p' },
    '240p': { 'next': '144p' },
    '144p': { 'next': None }
}

VIDEO_DEFINITIONS_ALIASES = {
    '4k': '2160p'
}

AUDIO_DEFINITIONS = {
    'max': { 'next': '160kbps' },
    '160kbps': { 'next': '128kbps' },
    '128kbps': { 'next': '70kbps' },
    '70kbps': { 'next': '50kbps' },
    '50kbps': { 'next': None }
}

AVAILABLE_DEFINITIONS = set()
for definition_group in [
    VIDEO_DEFINITIONS,
    VIDEO_DEFINITIONS_ALIASES,
    AUDIO_DEFINITIONS
]:
    for definition in definition_group:
        AVAILABLE_DEFINITIONS.add(definition)
