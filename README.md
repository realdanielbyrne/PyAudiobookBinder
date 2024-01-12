PyAudiobookBinder
=================
PyAudioBookBinder is a lightweight tool using ffmeg which simplifies the process of binding multiple audio files togethers
into an audiobook by gleaming smart defaults from the audio files's metadata, locations, durations, and names.

## Overview
PyAudiobookBinder is a lightweight wrapper around ffmpeg that can be used to bind mp3s together into an m4b audiobook. 
It sole purpose is to bind multiple audio files with metadata into a single M4B file. The utility is designed to  
simplify ffmpeg by eliminating the need to remember the ffmpeg command line options and to automate the most basic 
binding operations in a minimalistic way and to limit the amount of configuration options needing to be set by 
inferring most information from the audio files, their location, and by the company of files they keep.

To keep it simple, the title and author of the audiobook can be extracted from the directory name by default. If it
conforms to the pattern '{TitleOfBook}_{AuthorName}'. Furthermore, the program will automatically scan the folder 
for a cover art, infer the order of the MP3, calculate co comon bitrate from the existing files, and encode in final
composition with AAC. All of these options of course can be overridden if desired.

The files are bound together in the order they are found in the directory. PyAudiobookBinder assumes the chapters 
will begin with a zero leading numbering scheme, (01, 02 instead of 1,2). This is a requirement for automatic 
ordering so that the software can sort them. For instance, you should name the first chapter something like '01 - 
{Ch. Title}.mp3', and so on. Don't forget to use the leading zero for single digit chapter numbers, otherwise you 
will get chapters sorted like '1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9' instead of '01, 02, 03, 04, 05, 06, 07, 08, 
09, 10, 11'. 

If a number separator is provided, the chapter title will be extracted from the filename by removing the number
separator and everything before it. For example, if the number separator is ' - ' (space, dash, space), then the
chapter title will be extracted from the filename '01 - Chapter Title.mp3' as 'Chapter Title'. If no number separator
is provided, the chapter title will not be extracted from the filename. In this case, the chapter title will be
simply the filename without the extension.

sample usage: 

```shell
pybind -d "TomSawyer_MarkTwain" 
```


## Features
- **Automated File Ordering**: Automatically orders bound audio files alphabetically for seamless audiobook experience.
- **Automated Cover Art Handling**: Automatically detects and includes cover art from the directory.
- **Automated Bitrate Selection**: Maintains a consistent bitrate in the final M4B file.
- **Title and Author Detection**: Automatically infers title and author from the directory name.
- **Chapter Metadata**: Automatically adds chapter titles and breaks to the M4B file.
- **CLI Interface**: Simple command line interface for ease of use or import as a module.

## Requirements
- Python 3.x
- FFmpeg (The utility uses FFmpeg for audio processing)

This utility is simply a lightweight wrapper for FFmpeg. As such, FFmpeg must be installed on your system for PyAudiobookBinder to work. If you don't already have FFmpeg installed, you can download one of the prebuilt pacakges from the [official website](https://ffmpeg.org/download.html).  However, the simplest way to install FFmpeg is by using a package manager.

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

## Installation

1. Ensure Python 3.x and ffmpeg are installed on your system.
2. Clone or download this repository or install from PyPI.
3. Install required Python libraries if not using PyPi.

#### Install from PyPi

``` shell
pip install pyaudiobookbinder
```

## Usage
To use PyAudiobookBinder, navigate to the directory containing your MP3 files and execute the script with the necessary arguments. The basic command structure is:


``` shell
usage: pybind [-h] [-d DIRECTORY] [-t TITLE] [-a AUTHOR] [-c COVERIMAGE] [-e {aac,alac,flac,libmp3lame,mpeg4}] [-b BITRATE] [-n NUMBER_SEPARATOR]
```

## Examples
  
``` shell
pybind -d "TomSawyer_MarkTwain" 
```
The above commane binds MP3 in the directory ./TomSawyer_MarkTwain, extracts title and author from the directory name, 
sets the bitrate to common bitrate of the MP3 files, encodes the output file with aac, and attaches the cover art if
found in the directory. The output file will be named 'Tom Sawyer - Mark Twain.m4b' and will be located in the same
directory as the source files.

``` shell
pybind -d "TomSawyer_MarkTwain" -t "The Adventures of Tom Sawyer" -e "aac" -b 128 -c "tomsawyer.jpg"
```
The above command binds MP3 in the directory ./TomSawyer_MarkTwain, sets the title to 'The Adventures of Tom Sawyer',
sets the bitrate to 128 kbps, encodes the output file with aac, and attaches the cover art 'tomsawyer.jpg' located in
the same directory as the source files. The output file will be named 'The Adventures of Tom Sawyer - Mark Twain.m4b' and will be
located in the same directory as the source files.

More help can be found by running the command:

``` shell
pybind -h
```

## Contributing

If you would like to contribute to the development of PyAudiobookBinder, please follow these guidelines:
- Fork the repository.
- Make your changes in a separate branch.
- Submit a pull request with a description of the changes.

Development opportunities include:

- Adding support for more audio formats.
- Adding support for more metadata.
- Adding tests.
- Improving the CLI interface.

## License

MIT License Copyright (c) [2024] [Daniel Byrne]


---

