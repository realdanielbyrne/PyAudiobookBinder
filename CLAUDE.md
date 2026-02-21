# CLAUDE.md - AI Assistant Guide for PyAudiobookBinder

## Project Overview

PyAudiobookBinder is a lightweight Python CLI tool and library that combines multiple MP3 files into a single M4B audiobook file using FFmpeg. It infers metadata (title, author, bitrate, cover art, chapter info) from directory names, filenames, and audio file properties to minimize required configuration.

- **Version**: 0.7.0 (Beta)
- **License**: MIT
- **Python**: >=3.9
- **Author**: Daniel Byrne

## Repository Structure

```
PyAudiobookBinder/
├── CLAUDE.md                 # This file
├── LICENSE                   # MIT License
├── README.md                 # User-facing documentation
├── pyproject.toml            # Build config, dependencies, entry points
├── requirements.txt          # Dependencies (argparse only)
├── .gitignore
└── src/
    └── pyaudiobookbinder/
        ├── __init__.py               # Public API exports: pybind, PyAudiobookBinder
        └── pyaudiobookbinder.py      # All implementation (~635 lines)
```

The entire implementation lives in a single module: `src/pyaudiobookbinder/pyaudiobookbinder.py`.

## Build and Installation

**Build system**: setuptools (configured in `pyproject.toml`)

```shell
# Install from source (editable/development mode)
pip install -e .

# Install from PyPI
pip install pyaudiobookbinder
```

**System dependency**: FFmpeg must be installed separately (`ffmpeg` and `ffprobe` must be on PATH).

## Entry Points

- **CLI command**: `pybind` (defined in `pyproject.toml` `[project.scripts]`, maps to `pyaudiobookbinder:pybind`)
- **Programmatic API**: `from pyaudiobookbinder import PyAudiobookBinder, pybind`

## Architecture

### Core Class: `PyAudiobookBinder`

The main class that orchestrates audiobook creation. Constructor parameters:

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `directory` | str | `""` | Directory containing MP3 files |
| `title` | str | `""` | Audiobook title (auto-extracted from dir name if empty) |
| `author` | str | `""` | Author name (auto-extracted from dir name if empty) |
| `image` | str | `""` | Cover image path (auto-detected if empty) |
| `encoder` | str | `"aac"` | Audio encoder: aac, alac, flac, libmp3lame, mpeg4 |
| `bitrate` | int | `0` | Bitrate in kbps (0 = auto-detect most common) |
| `number_separator` | str | `""` | Separator for extracting chapter titles from filenames |

### Key Methods

- `extract_book_info_from_directory()` - Parses `{TitleInCamelCase}_{AuthorInCamelCase}` directory naming pattern
- `extract_title()` / `extract_author()` - Convenience wrappers for the above
- `find_cover_image()` - Looks for `cover.jpg` or `cover.png` in the source directory
- `get_common_bitrate()` - Determines most common bitrate across all MP3 files
- `get_bitrate(filename)` / `get_duration(filename)` - Query individual files via `ffprobe`
- `create_file_list()` - Generates `file_list.txt` for FFmpeg concat demuxer
- `create_chapters_file()` - Generates `chapters.txt` with timestamps
- `create_metadata_file()` - Generates `ffmetadata.txt` (FFMETADATA1 format)
- `merge()` - Executes the FFmpeg command to produce the final `.m4b` file

### CLI Function: `pybind()`

Parses arguments via `argparse` and instantiates `PyAudiobookBinder`. Includes Jupyter notebook detection for development use.

### Generated Files (during audiobook creation)

- `file_list.txt` - FFmpeg concat input list
- `chapters.txt` - Chapter timestamps and titles
- `ffmetadata.txt` - FFmpeg metadata file
- `{Title} - {Author}.m4b` - Final output audiobook

## Dependencies

**Python dependencies**: `argparse` (only explicit dependency; already in stdlib)

**Standard library usage**: `re`, `subprocess`, `json`, `os`, `glob`, `sys`, `datetime`, `collections.Counter`

**External tools** (must be installed on system):
- `ffmpeg` - Audio concatenation and encoding
- `ffprobe` - Audio metadata extraction (duration, bitrate)

## Testing

There are currently no tests in this project. The README lists "Adding tests" as a development opportunity. If adding tests:

- Use `pytest` as the test framework
- FFmpeg calls use `subprocess.check_output` and `subprocess.run` with `shell=True` -- these should be mocked in tests
- Key testable units: directory name parsing (`extract_book_info_from_directory`), bitrate detection, chapter/metadata file generation

## Code Conventions

- **Naming**: PascalCase for classes, snake_case for functions/variables, UPPERCASE for module-level constants
- **Strings**: f-strings throughout
- **File I/O**: Always uses `encoding='utf-8'`
- **Docstrings**: Google-style with `Args:` and `Returns:` sections on all public methods
- **Type hints**: Return type annotations on methods (e.g., `-> str`, `-> float`, `-> None`), but no parameter type annotations
- **Imports**: Standard library only, grouped at top of file without blank line separators
- **Cell markers**: `# %%` markers present (Jupyter notebook cell separators used during development)

## CI/CD

No CI/CD pipeline is configured. No GitHub Actions, Makefile, or tox configuration exists.

## Important Patterns

### Directory Naming Convention

The project uses a specific directory naming pattern for metadata extraction:
- Format: `{TitleOfBook}_{AuthorName}` in CamelCase
- Example: `TomSawyer_MarkTwain` → Title: "Tom Sawyer", Author: "Mark Twain"
- The `_` separates title from author; CamelCase boundaries become spaces
- Handles numeric prefixes: `2001ASpaceOdyssey` → "2001 A Space Odyssey"

### MP3 File Naming Convention

- Files must use zero-padded numbering: `01`, `02`, ..., `10`, `11` (not `1`, `2`, ...)
- With `number_separator=" - "`: `01 - Chapter Title.mp3` extracts "Chapter Title"
- Without separator: chapter title is the full filename without extension
- Files are sorted alphabetically, so zero-padding is critical for correct ordering

### FFmpeg Subprocess Calls

All FFmpeg/ffprobe interactions use `subprocess`:
- `subprocess.check_output(..., shell=True)` for `ffprobe` queries
- `subprocess.run(cmd, check=True)` for the final `ffmpeg` merge
- Output from ffprobe is parsed as JSON

## Common Development Tasks

```shell
# Install in development mode
pip install -e .

# Run the CLI
pybind -d "path/to/mp3/directory"

# Run with all options
pybind -d "BookTitle_AuthorName" -t "Custom Title" -a "Custom Author" -e aac -b 192 -c cover.jpg -n " - "
```
