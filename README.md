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

## Installation

To install MediaKit, you'll need to have [Python 3](https://www.python.org/downloads/) (>= 3.6) and [pip](https://pip.pypa.io/en/stable/installing/) already installed on your computer. With those packages available, run:

```bash
pip install mediakit
```

or

```bash
pip3 install mediakit
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


### Examples of use:

Download to the current directory
```bash
mediakit "https://www.youtube.com/watch?v=m7AFEULF9LI"
```

Download to **~/Videos**
```bash
mediakit "https://www.youtube.com/watch?v=m7AFEULF9LI" ~/Videos
```

Download to **~/Videos** with name **song.mp4**
```bash
mediakit "https://www.youtube.com/watch?v=m7AFEULF9LI" ~/Videos/song.mp4
```

---

Made by [Diego Aquino](https://github.com/diego-aquino/) :sunglasses:. [Connect with me!](https://www.linkedin.com/in/diego-aquino)
