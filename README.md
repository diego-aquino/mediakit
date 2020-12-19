<h1 align="center">
  Mediakit
</h1>

<p align="center">
  <i>
    <img align="center" src="./.github/icons/youtube.svg" height="20px" alt="YouTube">
    Download YouTube videos fast, directly from the command line
  </i>
</p>

<p align="center">
  <a
    href="https://pypi.org/project/mediakit/"
    target="_blank"
    rel="noopener noreferrer"
  >
    <img
      src="https://img.shields.io/pypi/v/mediakit.svg?color=108D94&label=PyPI"
      alt="Latest version on PyPI"
    >
  </a>
  <a
    href="https://pypi.org/project/mediakit/"
    target="_blank"
    rel="noopener noreferrer"
  >
    <img
      src="https://img.shields.io/pypi/dm/mediakit.svg?color=108D94"
      alt="Monthly downloads"
    >
  </a>
  <a
    href="https://github.com/diego-aquino/mediakit/graphs/contributors"
    target="_blank"
    rel="noopener noreferrer"
  >
    <img
      src="https://img.shields.io/github/contributors/diego-aquino/mediakit.svg?color=108D94"
      alt="Number of contributors"
    >
  </a>
  <a
    href="https://github.com/diego-aquino/mediakit/blob/main/LICENSE.txt"
    target="_blank"
    rel="noopener noreferrer"
  >
    <img
      src="https://img.shields.io/github/license/diego-aquino/mediakit.svg?color=108D94"
      alt="License"
    >
  </a>
</p>

<p align="center">
  <a href="#features">Features</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#installation">Installation</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#how-to-use">How to use</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#api-reference">API Reference</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#development-experiences">Development experiences</a>
</p>

---

**Mediakit** is a command line tool to download videos from YouTube.

<p align="center">
  <img src="./.github/demo.gif" alt="Downloading with Mediakit" width="650px">
</p>

## Features

- Quickly download YouTube videos with a single command on your terminal
- Select specific download formats (video, audio and video-only) if you want to, with resolutions as high as **4K** :sunglasses:

## Installation

To install Mediakit, you need [Python 3.6+](https://www.python.org/downloads/) and [pip](https://pip.pypa.io/en/stable/installing/) already installed on your computer. Then, run:

```bash
pip install mediakit
```

## How to use

You can download a video with Mediakit by running:

```bash
mediakit <video_url> [<output_path>]
```

- **video_url**: the URL of the video to download (e.g. http://www.youtube.com/watch?v=...).

  > As URL's may have special characters, it is recommended that you **wrap the URL in double quotes** ("") to ensure that it will be recognized properly.

- **output_path**: optional destination to where to save the downloads. If not provided, this will default to the current directory.

  > You can also provide a custom name for the downloaded file. To do that, include it in the output path (e.g. `path/to/folder/video.mp4`).

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

By default, Mediakit will download the specified video with the highest available resolution. However, you can select specific download formats with the flag `--formats` (or its shorthand `-f`), followed by one or more desired formats:

```bash
mediakit <video_url> [<output_path>] [-f | --formats]
```

You can also download as **audio** (`mp3`) or as **video only** (without audio) by using the format options **`audio`** and **`videoonly`**, respectively. If no resolution is provided with these options, Mediakit will download the media with highest quality, although you can select a specific resolution by adding it right after the option used (e.g. `-f audio 128kbps`). Check the examples bellow for more use details.

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

- Download as **audio** (`mp3`)
  ```bash
  mediakit "https://www.youtube.com/watch?v=m7AFEULF9LI" -f audio
  ```

- Download **multiple formats and resolutions** at once (each resolution will be downloaded in a different file)
  ```bash
  mediakit "https://www.youtube.com/watch?v=m7AFEULF9LI" -f 1080p audio videoonly 720p
  # download video with 1080p, audio with highest definition available and video-only (without audio) with 720p
  ```

### Downloading multiple videos sequentially

With the option `-b` (or its longhand `--batch`), you can download multiple videos sequentially by providing a batch file (a text file containing one or more video URL's, each one in a separate line):

```bash
mediakit [-b | --batch] <batch_file>
```

By running this, Mediakit will read all URL's in the provided file and download them sequentially.

> You can also use other options along with `--batch`, such as specify which formats and definitions you want your downloads to be.

**Examples of use:**

Using a batch file called `urls.txt` as an example:
  ```bash
  # contents of `urls.txt`
  https://www.youtube.com/watch?v=m7AFEULF9LI
  https://www.youtube.com/watch?v=tpWLeUt_7Cc
  https://www.youtube.com/watch?v=Fau8gKw33ME
  ```

- Download URL's in `urls.txt` with the highest available resolution
  ```bash
  mediakit -b urls.txt
  ```

- Download URL's in `urls.txt` as audio (**mp3**)
  ```bash
  mediakit -b urls.txt -f audio
  ```

---

## API Reference

Mediakit currently supports the following command options:

| Option | Description | Example |
|-:|-|-|
| `-h`, `--help` | Show help | `mediakit -h` |
| `-v`, `--version` | Show the currently installed version | `mediakit -v` |
| `-y`, `--yes` | Answer "yes" to all questions beforehand | `mediakit https://... -y` |
| `-b <batch_file>`, <br /> `--batch <batch_file>` | Download videos from URL's stored in a batch file | `mediakit -b urls.txt` |
| `-nc`, `--no-colors` | Disable the colors of the interface | `mediakit https://... -nc` |
| `-f <formats>`, <br /> `--formats <formats>` | Specify which formats you want to download | `mediakit https://... -f audio` |

---

## Development experiences

All experiences and learning acquired during the development of Mediakit are detailed in [Development experiences and learning](/docs/experiences-and-learning.md). Check it out if you want to know more about what were the motivations to build this project, how it was developed and what were the main challenges and experiences.

---

Made by [Diego Aquino](https://github.com/diego-aquino/) :sunglasses:. [Connect with me!](https://www.linkedin.com/in/diego-aquino)
