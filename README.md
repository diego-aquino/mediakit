<h1 align="center">
  MediaKit
</h1>

<p align="center">
  <i>Download YouTube videos fast, directly from the command line</i>
</p>

<p align="center">
  <a href="#features">Features</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#installation">Installation</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#how-to-use">How to use</a>
</p>

---

**MediaKit** is a command line tool for downloading videos from YouTube.

## Features

- Quickly download YouTube videos with a single command on your terminal
- Select specific download formats (video, audio and video-only) if you want to, with resolutions as high as **4K** :sunglasses:

## Installation

To install MediaKit, you'll need to have [Python 3.6+](https://www.python.org/downloads/) and [pip](https://pip.pypa.io/en/stable/installing/) installed on your computer. Then, run:

```bash
pip install mediakit
```

## How to use

You can download a video with MediaKit by running:

```bash
mediakit <video_url> [<output_path>]
```

- **video_url**: the URL of the video to download (e.g. http://www.youtube.com/watch?v=...).

    > As URL's may have special characters, it is recommended that you **wrap the URL in double quotes** ("") to ensure that it will be recognized properly.

- **output_path**: optional destination folder to where to save the downloads. If not provided, this will default to the current directory.

    > You can also provide a custom name for the downloaded file. To do that, include it in the output path (e.g. path/to/folder/video.mp4).

After running this command, an interactive CLI will guide you through the download process.

**Examples of use:**
  - Download to the current directory
    ```bash
    mediakit "https://www.youtube.com/watch?v=m7AFEULF9LI"
    ```

  - Download to **~/Videos**
    ```bash
    mediakit "https://www.youtube.com/watch?v=m7AFEULF9LI" ~/Videos
    ```

  - Download to **~/Videos** with name **song.mp4**
    ```bash
    mediakit "https://www.youtube.com/watch?v=m7AFEULF9LI" ~/Videos/song.mp4
    ```

### Selecting specific download formats

By default, MediaKit will download the specified video with the highest available resolution. However, you can select specific download formats with the flag `--formats` (or its shorthand `-f`), followed by one or more desired formats:

```bash
mediakit <video_url> [<output_path>] [-f | --formats]
```

You can also download the audio (as `mp3`) or the video without audio by using the format options **`audio`** and **`videoonly`**, respectively. If no resolution is provided, MediaKit will download the media with highest quality, although you can select a specific resolution by adding it right after the option used (e.g. `-f audio 128kbps`). Check the examples bellow for more use details.

> If a resolution is not available for the video, the download will fall back to the closest available resolution lower than the one specified.

**Examples of use:**
- Download with resolution of **1080p**
  ```bash
  mediakit "https://www.youtube.com/watch?v=m7AFEULF9LI" -f 1080p
  ```

- Download with resolution of **4K** (2160p)
  ```bash
  mediakit "https://www.youtube.com/watch?v=m7AFEULF9LI" -f 4K
  ```

- Download **multiple resolutions** at once (each resolution will be downloaded in a different file)
  ```bash
  mediakit "https://www.youtube.com/watch?v=m7AFEULF9LI" -f 1080p 720p
  ```

- Download with the **highest resolution available** (same result as not using the flag `-f`)
  ```bash
  mediakit "https://www.youtube.com/watch?v=m7AFEULF9LI" -f max
  ```

- Download **audio** (as `mp3`)
  ```bash
  mediakit "https://www.youtube.com/watch?v=m7AFEULF9LI" -f audio
  ```

- Download **multiple formats and resolutions** at once (each resolution will be downloaded in a different file)
  ```bash
  mediakit "https://www.youtube.com/watch?v=m7AFEULF9LI" -f 1080p audio videoonly 720p
  # download video with 1080p, audio with highest definition available and video-only (without audio) with 720p
  ```

---

Made by [Diego Aquino](https://github.com/diego-aquino/) :sunglasses:. [Connect with me!](https://www.linkedin.com/in/diego-aquino)
