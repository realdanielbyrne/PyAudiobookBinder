PyAudiobookBinder
---

### Overview
PyAudiobookBinder is a Python-based utility that binds multiple MP3 audio files into a single M4B audiobook file. This tool simplifies the process of creating audiobooks by automating tasks such as ordering the files, selecting a bitrate, and adding cover art, author, title, and chapter metadata. The idea behind this tool was to create a simple wrapper to eliminate the need to remember the ffmpeg command line options and to automate the most basic binding operations in a minimalistic way.


### Features
- **Automated File Ordering**: Orders audio files alphabetically for seamless audiobook experience.
- **Automated Cover Art Handling**: Automatically detects and includes cover art from the directory.
- **Automated Bitrate Selection**: Maintains a consistent bitrate in the final M4B file.
- **Title and Author Detection**: Infers title and author from the directory name.
- **Chapter Metadata**: Automatically adds chapter titles and breaks to the M4B file.

### Requirements
- Python 3.x
- FFmpeg (The utility uses FFmpeg for audio processing)

This utility is simply a lightweight wrapper for FFmpeg. As such, FFmpeg must be installed on your system for PyAudiobookBinder to work. If you don't already have FFmpeg installed, you can download one of the prebuilt pacakges it from the [official website](https://ffmpeg.org/download.html).  However, the simplest way to install FFmpeg is by using a package manager.

#### MacOS ffmpeg Installation Using Homebrew

On a macOS system, the easiset way you can install FFmpeg is by using [Homebrew](https://brew.sh/) the Mac package manager which makes the installation process criminally easy.

``` shell
brew install ffmpeg
```

#### Windows ffmpeg Installation Using Chocolatey

On a Windows system, likewise, the simplest installation method involves using a Windows package manager.  The best Windows pacakge manager is [Chocolatey](https://chocolatey.org/), and I say that because I don't know of another one.  I apologize in advance for the development teams out there whove develoepd a better Windows package manager that I just haven't heard about.

``` shell
choco install ffmpeg
```

#### Linux ffmpeg Installation Using APT

On a Linux system, you can install FFmpeg using the APT package manager.  The installation process is pretty straightforward.

``` shell
sudo apt install ffmpeg
```

### Installation
pip install pyaudiobookbinder

### Usage
To use PyAudiobookBinder, navigate to the directory containing your MP3 files and execute the script with the necessary arguments. The basic command structure is:

``` shell
pybind [arguments]
```

``` shell
usage: pybind [-h] [-d DIRECTORY] [-t TITLE] [-a AUTHOR] [-e ENCODER] [-b BITRATE]
```





#### Contributing
If you would like to contribute to the development of PyAudiobookBinder, please follow these guidelines:
- Fork the repository.
- Make your changes in a separate branch.
- Submit a pull request with a description of the changes.

#### License
MIT License Copyright (c) [2024] [Daniel Byrne]


---

