from .utils.ffmpeg import get_ffmpeg_binary


FFMPEG_BINARY = get_ffmpeg_binary()

VIDEO_RESOLUTIONS = {
    '2160p': { 'next': '1440p' },
    '1440p': { 'next': '1080p' },
    '1080p': { 'next': '720p' },
    '720p': { 'next': '480p' },
    '480p': { 'next': '360p' },
    '360p': { 'next': '240p' },
    '240p': { 'next': '144p' },
    '144p': { 'next': None }
}

VIDEO_RESOLUTIONS_ALIASES = {
    '4k': '2160p'
}
