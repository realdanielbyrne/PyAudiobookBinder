# %%
import re
import subprocess, json, os, glob, sys
import datetime
from collections import Counter
import argparse
from argparse import RawTextHelpFormatter


encoders = ["aac", "alac", "flac", "libmp3lame", "mpeg4"]

description = """
Description:
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
    pybind -d "TomSawyer_MarkTwain" 
  
  The above commane binds MP3 in the directory ./TomSawyer_MarkTwain, extracts title and author from the directory name, 
  sets the bitrate to common bitrate of the MP3 files, encodes the output file with aac, and attaches the cover art if
  found in the directory. The output file will be named 'Tom Sawyer - Mark Twain.m4b' and will be located in the same
  directory as the source files.
  
"""
#%%
class PyAudiobookBinder:
    """
    Args:
      directory (str): The directory path containing the MP3 files to be concatenated into an M4B file. Defaults to the 
      current directory. The directory name will be used as the output file name if one is nor provided. The directory 
      can contain the Title of the book followed by an underscore and then the Author's name. For example if the
      directory name was 'TomSawyer_MarkTwain', the output file would be named 'TomSawyer_MarkTwain.m4b', the metadata
      Title would equal 'Tom Sawyer', and Author would be 'Mark Twain'

      title (str): The title of the audiobook. If not provided, it will be extracted from the directory name. The
        containing directory name should conform to the pattern '{TitleOfBook}_{Author'sName}' in order for the title to
        be extracted correctly. Each word in the title should be capitalized.  For example, 'TomSawyer_MarkTwain' would
        be extracted as 'Tom Sawyer'.

      author (str): The author of the audiobook. If not provided, it will be extracted from the directory name. The
        containing directory name should conform to the pattern '{TitleOfBook}_{Author'sName}' in order for the author to
        be extracted correctly. Each word in the author's name should be capitalized.  For example, 'TomSawyer_MarkTwain'
        would be extracted as 'Mark Twain'.

      image (str): The path to the cover image file (JPEG or PNG) for the audiobook. If not provided, the program will
        look for cover.jpg or cover.png in the source directory, and if found this image wil be used.  Basically, if you
        have a cover image in the source directory, you don't need to specify it here as long as it is named cover.jog or
        cover.png.

      encoder (str): The audio encoder to be used for the M4B file. Defaults to 'aac'. Valid encoders are: 'aac', 'alac',
        'flac', 'libmp3lame', and 'mpeg4'.

      bitrate (int): The bitrate to be used for the M4B file. Defaults to the most common bitrate among the MP3 files in
        the directory. for instance, if the directory contains 128k, 192k, and 192k mp3 files, the output file will be
        encoded at 192k.

    """

    def __init__(
        self, directory="", title="", author="", image="", encoder="aac", bitrate=0, number_separator=""
    ) -> None:
        if directory == "" or directory == ".":
            directory = os.getcwd()
        self.directory = directory

        files_list = [f for f in os.listdir(self.directory) if f.endswith(".mp3")]
        if files_list == []:
            print(f"No MP3 files found in {self.directory}")
            sys.exit(0)

        if encoder not in encoders:
            raise ValueError(
                f"Invalid encoder: {encoder}.  Valid encoders are: {encoders}"
            )
            
        self.encoder = encoder
        
        if title == "":
            self.title = self.extract_title()
            print(f"Title: {self.title}")

        if author == "":
            self.author = self.extract_author()
            print(f"Author: {self.author}")

        if image == "":
            self.image = self.find_cover_image()
            print(f"Cover image: {self.image}")

        if bitrate == 0:
            self.bitrate = self.get_common_bitrate()

        self.number_separator = number_separator
        self.file_list_path = self.create_file_list()
        self.chapters_file_path = self.create_chapters_file()
        self.meta_filepath = self.create_metadata_file()

        self.output_filename = os.path.join(
            self.directory, os.path.basename(self.directory)
        )

    def create_metadata_file(self, number_separator="") -> str:
        """
        Creates a metadata file for the audiobook.

        Args:
            numberSeparator (str): The character(s) used to separate the chapter number from the chapter title in the MP3 filenames.
              For example, if the MP3 filenames are '01 - Chapter Title.mp3', '02 - Chapter Title.mp3', etc., then the numberSeparator
              would be ' - ' (space, dash, space). Defaults to an empty string.

        Returns:
            string: The filepath of the created metadata file.
        """

        if not os.path.exists(self.chapters_file_path):
            self.create_chapters_file(self.directory)

        chapters = list()
        pattern = re.compile(r"(\d+ day[s]?, )?(\d+):(\d+):(\d+)\.\d{3}\s+(.*)")

        with open(self.chapters_file_path, "r") as f:
            for line in f:
                x = pattern.match(line)
                if x:
                    # Extracting days, hours, minutes, seconds, and chapter name
                    days, hrs, mins, secs, title = x.groups()
                    days = int(days.split()[0]) if days else 0
                    hrs = int(hrs) + days * 24  # Convert days to hours and add to hours
                    mins = int(mins)
                    secs = int(secs)

                    minutes = (hrs * 60) + mins
                    seconds = secs + (minutes * 60)
                    timestamp = seconds * 1000
                    chap = {"title": title, "startTime": timestamp}
                    chapters.append(chap)

        text = ";FFMETADATA1\n"
        text += f"title={self.title}\n"
        text += f"album={self.title}\n"
        text += f"artist={self.author}\n"
        text += f"authors={self.author}\n"
        text += f"genre=Audiobooks\n"
        for i in range(len(chapters) - 1):
            chap = chapters[i]
            title = chap["title"]
            start = chap["startTime"]
            end = chapters[i + 1]["startTime"] - 1
            text += (
                f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={start}\nEND={end}\ntitle={title}\n"
            )

        meta_filepath = os.path.join(self.directory, "ffmetadata.txt")
        with open(meta_filepath, "w") as myfile:
            myfile.write(text)

        print("Created metadata file ffmetadata.txt")
        return meta_filepath

    def get_filename_without_extension(self, filepath) :
        """
        Extracts the filename without extension from the given filepath.

        Args:
            filepath (string): The path to the file.

        Returns:
            string: The filename without extension.
        """
        # Extract the base filename with extension
        filename_with_ext = os.path.basename(filepath)
        # Split the filename and extension, and return just the filename
        filename_without_ext = os.path.splitext(filename_with_ext)[0]
        return filename_without_ext

    def create_chapters_file(self) -> str:
        """
        Creates a chapters file which deliniates the chapter breaks in the audiobook

        Args:
            directory (str): The directory path where the MP3 files are located.
            numberSeparator (str): The character(s) used to separate the chapter number from the chapter title in the MP3 filenames.
              For example, if the MP3 filenames are '01 - Chapter Title.mp3', '02 - Chapter Title.mp3', etc., then the numberSeparator
              would be ' - ' (space, dash, space). Defaults to an empty string.

        Returns:
            string: The filepath of the created chapters file.
        """
        if self.directory == "":
            self.directory = os.getcwd()

        # List all MP3 files
        files_list = [f for f in os.listdir(self.directory) if f.endswith(".mp3")]
        if files_list == []:
            print(f"No MP3 files found in {self.directory}")
            sys.exit(-1)

        files_list.sort()

        rawChapters = list()
        currentTimestamp = 0
        for file in files_list:
            title = self.get_filename_without_extension(file)
            if self.number_separator != "":
                title = self.number_separator.join(title.split(self.number_separator)[1:])

            filepath = os.path.join(self.directory, file)
            audioLength = self.get_duration(filepath)
            time = str(datetime.timedelta(seconds=currentTimestamp)) + ".000"
            rawChapters.append(time + " " + title)
            currentTimestamp = int(currentTimestamp + audioLength)

        chapters_filepath = os.path.join(self.directory, "chapters.txt")
        if not os.path.exists(chapters_filepath):
            print(f"Creating chapters file {chapters_filepath} ...")
            with open(chapters_filepath, "w") as chaptersFile:
              for chapter in rawChapters:
                chaptersFile.write(chapter + "\n")
        return chapters_filepath

    def get_duration(self, filename) -> float:
        """
        Retrieves the duration of the audio file in seconds by probing the file with ffprobe.

        Args:
            filename (string): The path to the audio file.

        Returns:
            float: The duration in seconds.
        """
        result = subprocess.check_output(
            f'ffprobe -v error -show_format -of json "{filename}"', shell=True
        ).decode()
        fields = json.loads(result)["format"]
        return float(fields["duration"])

    def get_bitrate(self, filename) -> int:
        """
        Retrieves the bitrate of the audio file in kilobits per second (kbps) by reading

        Args:
            filename (string): The path to the audio file.

        Returns:
            int: The bitrate in kbps.
        """
        result = subprocess.check_output(
            f'ffprobe -v error -show_format -of json "{filename}"', shell=True
        ).decode()
        fields = json.loads(result)["format"]

        if "bit_rate" not in fields:
            return 128
        bitrate = int(fields["bit_rate"]) // 1000
        return bitrate

    def get_common_bitrate(self) -> int:
        """
        Retrieves the most common bitrate among the MP3 files in the directory.
        For instance if the directory contains 128k, 192k, and 192k mp3 files, the output
        file will be encoded at 192k.

        Returns:
            int: The most common bitrate in kbps.
        """
        mp3_files = sorted(
            [
                os.path.join(self.directory, f)
                for f in os.listdir(self.directory)
                if f.endswith(".mp3")
            ]
        )
        if mp3_files == []:
            print(f"No MP3 files found in {self.directory}")
            sys.exit(0)

        bitrates = [self.get_bitrate(file) for file in mp3_files]
        print(f"Detected bit rates:{bitrates}")
        most_common_bitrate = Counter(bitrates).most_common(1)[0][0]
        print(f"Most common bit rate: {most_common_bitrate}k\n")
        return most_common_bitrate

    def extract_book_info_from_directory(self, directory_name)  -> tuple[str, str]:
        """
        Extracts the title and author of the audiobook from the directory name. The directory name
        should conform to the pattern '{TitleOfBook}_{AuthorName}' in order for the title and author
        to be extracted correctly. Each word in the title and author's name should be capitalized.
        For example, 'TomSawyer_MarkTwain' would be extracted as 'Tom Sawyer' and 'Mark Twain'.

        Args:
            directory_name (string): The name of the directory containing the audiobook files.

        Returns:
            tuple: The title and author of the audiobook as a tuple.
        """
        
        # If the directory name is empty, return empty strings
        if not directory_name:
            return "Unknown Title", "Unknown Author"
          
        # Extracting the last part of the directory name
        name_part = directory_name.split("/")[-1]

        # Separating title and author based on underscore
        parts = name_part.split("_")

        # Function to add space before capital letters and strip leading spaces
        def add_spaces(s):
            return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s).strip()

        # Enhanced function to handle titles like '2001ASpaceOdyssey'
        def format_title(title):
            title_with_spaces = add_spaces(title)
            # Special handling for cases like '2001A' to '2001 A'
            return re.sub(r"(\d+)([A-Z])", r"\1 \2", title_with_spaces)

        # Extracting title and author, considering cases with and without author
        title = format_title(parts[0]) if parts[0] else ""
        author = add_spaces(parts[1]) if len(parts) > 1 else ""

        return title, author

    def extract_title(self) -> str:
        """
        Extracts the title of the audiobook from the directory name. The directory name
        should conform to the pattern '{TitleOfBook}_{AuthorName}' in order for the title to be
        extracted correctly. Each word in the title should be capitalized. For example,
        'TomSawyer_MarkTwain' would yield 'Tom Sawyer'.

        Returns:
            string: The title of the audiobook.
        """
        title, _ = self.extract_book_info_from_directory(self.directory)
        return title

    def extract_author(self) -> str:
        """
        Extracts the author of the audiobook from the directory name. The directory name
        should conform to the pattern '{TitleOfBook}_{AuthorName}' in order for the author to be
        extracted correctly. Each word in the author's name should be capitalized. For example,
        'TomSawyer_MarkTwain' would yield 'Mark Twain'.

        Returns:
            string: The author of the audiobook.
        """
        _, author = self.extract_book_info_from_directory(self.directory)
        return author

    def find_cover_image(self) -> str:
        """
        Searches for a cover image file (JPEG or PNG) in the directory. If found, the path to the
        cover image file is returned. If not found, an empty string is returned.
        The cover image file should be named 'cover.jpg' or 'cover.png' for it to be found.
        Returns:
            string: The path to the cover image file if found, otherwise an empty string.
        """
        # Define the patterns for the file names
        patterns = ["cover.jpg", "cover.png"]

        # Search for files in the specified directory
        for pattern in patterns:
            file_list = glob.glob(os.path.join(self.directory, pattern))
            if file_list:
                return file_list[0]  # Return first match
        return ""

    def create_file_list(self) -> str:
        """ Creates a file list containing the paths of the MP3 files in the directory.
        The file list is used as input to ffmpeg when binding the MP3 files into an M4B file.

        Returns:
            string: The filepath of the created file list.
        """
        mp3_files = sorted(
            [f for f in os.listdir(self.directory) if f.endswith(".mp3")]
        )

        # exit and return ampty string if no mp3_files found
        if mp3_files == []:
            print(f"No MP3 files found in {self.directory}")
            sys.exit(0)

        file_list_path = os.path.join(self.directory, "file_list.txt")
        if not os.path.exists(file_list_path):
            print(f"Creating file list {file_list_path} ...")
            with open(file_list_path, "w") as file:
                for mp3_file in mp3_files:
                    file.write(f"file '{mp3_file}'\n")
        return file_list_path

    def merge(self) -> None:
        """ Combines the MP3 files into a single M4B file using ffmpeg."""

        print("Combining files using ffmpeg ...\n")

        # build ffmpeg command
        ffmpeg_cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",self.file_list_path]
                        
        # import image
        if self.image != "" and os.path.exists(self.image):
            ffmpeg_cmd.extend(["-i", self.image])
            
        # import metadata
        if self.meta_filepath != "" and os.path.exists(self.meta_filepath):
            ffmpeg_cmd.extend(["-i", self.meta_filepath])
        
        # map audio streams
        ffmpeg_cmd.extend(["-map","0:a"]) 
        i = 1
        
        # map image
        if self.image != "" and os.path.exists(self.image):
          ffmpeg_cmd.extend(["-map",f"{i}:v"])
          i = i+1

        # map metadata
        if self.meta_filepath != "" and os.path.exists(self.meta_filepath):
            ffmpeg_cmd.extend(["-map_metadata", f'{i}'])
                
        ffmpeg_cmd.extend([  
                "-c:a",
                f"{self.encoder}",
                "-c:v",
                "copy",
                "-disposition:v:0",
                "attached_pic",
                "-b:a",
                f"{self.bitrate}k",
                "-threads",
                "0",
                "-fps_mode:a",
                "auto",
                f"{os.path.join(self.directory, f'{self.title} - {self.author}')}.m4b"
            ])
        
        # Convert all elements to strings and join them with spaces to print out the command
        array_as_string = ' '.join([str(element) for element in ffmpeg_cmd])
        print(f"\n{array_as_string}\n")

        subprocess.run(ffmpeg_cmd)


# %%
# function to determine if we are runnign in ipython notebook
def is_notebook() -> bool:
    try:
        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False  # Probably standard Python interpreter


def pybind() -> None:
    # parse command line arguments
    parser = argparse.ArgumentParser(description=description,formatter_class=RawTextHelpFormatter)
    
    parser.add_argument(
        "-d",
        "--directory",
        default=".",
        help=        
"""The directory path containing the MP3 files to be concatenated into an M4B file. Defaults to the current directory. The directory name will 
be used as the output file name if one is nor provided. The directory name can contain the Title of the book followed by an underscore and then 
the Author's name. For example if the directory name was 'TomSawyer_MarkTwain', the output file would be named 'TomSawyer_MarkTwain.m4b', 
the metadata Title be interpreted as 'Tom Sawyer' and Author as 'Mark Twain'.

""",
    )

    parser.add_argument(
        "-t",
        "--title",
        action="store",
        type=str,
        default="",
        help=
"""The title of the audiobook. If not provided, it will be extracted from the directory name. The containing directory name should conform to the pattern
'{TitleOfBook}_{AuthorsName}' in order for the title to be extracted correctly. Each word in the title should be capitalized.  For example, 
'TomSawyer_MarkTwain' would be extracted as 'Tom Sawyer'.

""",
    )

    parser.add_argument(
        "-a",
        "--author",
        action="store",
        type=str,
        default="",
        help=
"""The author of the audiobook. If not provided, it will be extracted from the directory name. The containing directory name should conform to the pattern 
'{TitleOfBook}_{AuthorsName}' in order for the author to be extracted correctly. Each word in the author's name should be capitalized.  For example, 
'TomSawyer_MarkTwain' would be extracted as 'Mark Twain'.

""",
    )

    parser.add_argument(
        "-c",
        "--coverimage",
        action="store",
        type=str,
        default="",
        help=
"""The path to the cover art of the book.  If not provided, this software will look for cover.jpg or cover.png in the source directory, and if found this 
image wil be atached to the m4b ourput file. If nott found and not specified here, no image will be included'.

""",
    )

    parser.add_argument(
        "-e",
        "--encoder",
        action="store",
        type=str,
        default="aac",
        help="""The audio encoder to be used for the M4B file. AAC is the default for a compressed audiobook. FLAC is the standard for an uncompressed audiobook.

""",
        choices=["aac", "alac", "flac", "libmp3lame", "mpeg4"],
    )

    parser.add_argument(
        "-b",
        "--bitrate",
        action="store",
        type=int,
        default=0,
        help=
"""The bitrate to be used for the M4B file. Defaults to the most common bitrate among the MP3 files in the directory. For example, if the directory contains
128k, 192k, and 192k mp3 files, the output file will be encoded at 192k.

""",
    )
    
    parser.add_argument(
      "-n",
      "--number_separator",
      action="store",
      type=str,
      default="",
      help=
"""The character(s) used to separate the chapter number from the chapter title in the MP3 filenames. For example, if the MP3 filenames are '01 - Chapter Title.mp3',
'02 - Chapter Title.mp3', etc., then the number separator would be ' - ' (space, dash, space) and title would be extracted as 'Chapter Title'. If no number 
separator is provided, the chapter title will simply be the filename without the extension.

""",          
    )

    if is_notebook():
        # for running in a notebook or vscode
        a = parser.parse_args("")
        directory = "../../tests/ToSleepInASeaOfStars_ChristopherPaolini"  # change this line to the directory containing the mp3 files
    else:
        a = parser.parse_args()
        directory = a.directory

    converter = PyAudiobookBinder(
        directory, a.title, a.author, a.coverimage, a.encoder, a.bitrate, a.number_separator
    )
    converter.merge()
    print("Done!")


if __name__ == "__main__":
    pybind()

# %%
