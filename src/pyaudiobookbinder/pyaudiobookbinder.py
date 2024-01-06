#%%
import re
import subprocess, json, os, glob, sys 
import datetime
from collections import Counter
from pprint import pprint
import argparse

#%%

encoders = ['aac', 'alac', 'flac', 'libmp3lame', 'mpeg4']
class PyAudiobookBinder:
  """
  PyAudiobookBinder is a lightweight wrapper around ffmpeg that can be used to bind mp3s together into an audiobook.
  It sole purpose is to bind multiple audio files and a book cover image to create an audiobook in a single M4B file.
  
  The program attempts to limit the amount of configuration opitons needing to be set by gleaming on each run by inferring
  most information from the audio files. To keep it simple the title and autor of the audiobook can be extracted from the 
  directory name if it conforms to the pattern '{TitleOfBook}_{AuthorName}'. Furthermore, the program will scan the folder
  for a cover art, order the MP3 files alphabetically, by the filename, keep the bitrate of the final file the same as the
  most common bitrate of the MP3 files, and use the AAC encoder by default. All of these options can be overridden if desired. 
    
  The files are bound together in the order they are found in the directory.  So the first file in the directory will be the first chapter
  in the audiobook, the second file will be the second chapter, and so on.  The files should be named in such a way that they will be sorted
  in the correct order.  For instance, the first chapter should be named '01 - Chapter Title.mp3' then '02 - Chapter Title.mp3' and so on.
  Don't forget to use the leading zero for single digit chapter numbers so that the files will be sorted correctly, otherwise you will get 
  chapters sorted like '1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9' instead of '01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11'. 
  
  The idea behind this tool was to create a simple wrapper to eliminate the need to remember the ffmpeg command line options and to automate the
  most basic binding operations in a minimalistic way. 

  Args:
    directory (str): The directory path where the MP3 files are located. Defaults to the current working directory if not provided.
    
    title (str): The title of the audiobook. If not provided, it will be extracted from the directory name. The containing directory name
      should conform to the pattern '{TitleOfBook}_{Author'sName}' in order for the title to be extracted correctly. Each word in the title should 
      be capitalized.  For example, 'TomSawyer_MarkTwain' would be extracted as 'Tom Sawyer'.
      
    author (str): The author of the audiobook. If not provided, it will be extracted from the directory name. The containing directory name
      should conform to the pattern '{TitleOfBook}_{Author'sName}' in order for the author to be extracted correctly. Each word in the author's name should
      be capitalized.  For example, 'TomSawyer_MarkTwain' would be extracted as 'Mark Twain'.
      
    image (str): The path to the cover image file (JPEG or PNG) for the audiobook. If not provided, the program will look for
      cover.jpg or cover.png in the source directory, and if found this image wil be used.  Basically, if you have a cover image
      in the source directory, you don't need to specify it here as long as it is named cover.jog or cover.png.
    
    encoder (str): The audio encoder to be used for the M4B file. Defaults to 'aac'. Valid encoders are: 'aac', 'alac', 'flac', 'libmp3lame', and 'mpeg4'.
    
    bitrate (int): The bitrate to be used for the M4B file. Defaults to the most common bitrate among the MP3 files in the directory.
      for instance, if the directory contains 128k, 192k, and 192k mp3 files, the output file will be encoded at 192k.
    

  Attributes:
    directory (str): The directory path where the MP3 files are located.
    title (str): The title of the audiobook.
    author (str): The author of the audiobook.
    image (str): The path to the cover image file for the audiobook.
    encoder (str): The audio encoder used for the M4B file.
    output_filename (str): The output filename for the M4B file.

  Methods:
    create_metadata_file(numberSeparator=''):
      Creates a metadata file for the audiobook.
      Returns the filepath of the created metadata file.

    get_filename_without_extension(filepath):
      Extracts the filename without extension from the given filepath.
      Returns the filename without extension.

    create_chapters_file(numberSeparator=''):
      Creates a chapters file which deliniates the chapter breaks in the audiobook
      based upon the length and order of the constituent MP3 files.
      Returns the filepath of the created chapters file.

    get_duration(filename):
      Retrieves the duration of the audio file in seconds by probing the file with ffprobe.
      Returns the duration in seconds.

    get_bitrate(filename):
      Retrieves the bitrate of the audio file in kilobits per second (kbps) by reading
      the metdata with ffprobe.
      Returns the bitrate in kbps.

    get_common_bitrate():
      Retrieves the most common bitrate among the MP3 files in the directory.
      For instance if the directory contains 128k, 192k, and 192k mp3 files, the output 
      file will be encoded at 192k.
      Returns the most common bitrate in kbps.

    extract_book_info_from_directory(directory_name):
      Extracts the title and author of the audiobook from the directory name. The directory name
      should conform to the pattern '{TitleOfBook}_{AuthorName}' in order for the title and author
      to be extracted correctly. Each word in the title and author's name should be capitalized.
      Returns the title and author as a tuple.

    extract_title():
      Extracts the title of the audiobook from the directory name. The directory name
      should conform to the pattern '{TitleOfBook}_{AuthorName}' in order for the title to be
      extracted correctly. Each word in the title should be capitalized. For example, 
      'TomSawyer_MarkTwain' would yield 'Tom Sawyer'.
      Returns the title.

    extract_author():
      Extracts the author of the audiobook from the directory name. The directory name
      should conform to the pattern '{TitleOfBook}_{AuthorName}' in order for the author to be
      extracted correctly. Each word in the author's name should be capitalized. For example,
      'TomSawyer_MarkTwain' would yield 'Mark Twain'.
      Returns the author.

    find_cover_image():
      Searches for a cover image file (JPEG or PNG) in the directory. If found, the path to the
      cover image file is returned. If not found, an empty string is returned.
      The cover image file should be named 'cover.jpg' or 'cover.png' for it to be found.
      Returns the path to the cover image file if found, otherwise an empty string.

    create_file_list():
      Creates a file list containing the paths of the MP3 files in the directory.
      The file list is used as input to ffmpeg when binding the MP3 files into an M4B file.
      The file list is sorted alphabetically by filename.  This is important because the
      order of the files in the file list determines the order of the chapters in the M4B file.
      So the Chpter 1 MP3 file should be named '01 - Chapter Title.mp3' then '02 - Chapter Title.mp3'
      and so on. Don't forget to use the leading zero for single digit chapter numbers so that the
      files will be sorted correctly.    
      Returns the filepath of the created file list.

    merge():
      Combines the MP3 files into a single M4B file using ffmpeg.

    add_meta():
      Adds metadata to the M4B file.

    combine_mp3_to_m4b():
      Combines the MP3 files into a single M4B file, adds metadata, and performs cleanup.

  """
  # Rest of the code...
class PyAudiobookBinder:
  

  def __init__(self, directory='', title='', author='', image='', encoder = 'aac', bitrate = 0):    
    if directory == '' or directory == '.':
      directory = os.getcwd()      
    self.directory = directory
    
    if encoder not in encoders:
      raise ValueError(f"Invalid encoder: {encoder}.  Valid encoders are: {encoders}")
    
    if title == '':
      title = self.extract_title()
      
    if author == '':
      author = self.extract_author()
    
    if image == '':
      image = self.find_cover_image()
      
    if bitrate == 0:
      bitrate = self.get_common_bitrate()
      
    self.file_list_path = self.create_file_list()
    self.chapters_file_path = self.create_chapters_file()
    self.meta_filepath = self.create_metadata_file()
      
    self.title = title
    self.author = author
    self.image = image
    self.encoder = encoder
    self.bitrate = bitrate
    self.output_filename = os.path.join(self.directory, os.path.basename(self.directory))

  '''
  This method is the workhorse of the class. It combines the MP3 files into a single M4B file,
  adds metadata, and performs cleanup.
  '''
  def combine_mp3_to_m4b(self):    
    self.merge()
    self.add_meta()

    # Remove temp files
    if os.path.exists(f'{os.path.join(self.directory, os.path.basename(self.directory))}.m4b'):
      os.remove(f'{os.path.join(self.directory, os.path.basename(self.directory))}.m4b')

    if os.path.exists(self.file_list_path):
      os.remove(self.file_list_path)

    if os.path.exists(self.meta_filepath):
      os.remove(self.meta_filepath)

    if os.path.exists(self.chapters_file_path):
      os.remove(self.chapters_file_path)

    print(f"\nDone!\n")

  '''
  Creates a metadata file for the audiobook. The metadata file is used by ffmpeg to add metadata
  to the M4B file. The metadata file is named ffmetadata.txt, and it will be stored in the source
  directory.
  '''
  def create_metadata_file(self, numberSeparator=''):
    chapter_filepath = os.path.join(self.directory, "chapters.txt")
    if not os.path.exists(chapter_filepath):
      self.create_chapters_file(self.directory, numberSeparator)

    chapters = list()
    with open(chapter_filepath, 'r') as f:
      for line in f:
        x = re.match(r"(\d*):(\d{2}):(\d{2}).(\d{3}) (.*)", line)
        hrs = int(x.group(1))
        mins = int(x.group(2))
        secs = int(x.group(3))
        title = x.group(5)

        minutes = (hrs * 60) + mins
        seconds = secs + (minutes * 60)
        timestamp = (seconds * 1000)
        chap = {
          "title": title,
          "startTime": timestamp
        }
        chapters.append(chap)

    text = ";FFMETADATA1\n"
    text += f"title={self.title}\n"
    text += f"album={self.title}\n"
    text += f"artist={self.author}\n"
    text += f"authors={self.author}\n"
    for i in range(len(chapters) - 1):
      chap = chapters[i]
      title = chap['title']
      start = chap['startTime']
      end = chapters[i + 1]['startTime'] - 1
      text += f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={start}\nEND={end}\ntitle={title}\n"

    meta_filepath = os.path.join(self.directory, "ffmetadata.txt")
    with open(meta_filepath, "w") as myfile:
      myfile.write(text)

    print('Created metadata file ffmetadata.txt')
    return meta_filepath

  '''
  Extracts the filename without extension from the given filepath.
  '''
  def get_filename_without_extension(self, filepath):
    # Extract the base filename with extension
    filename_with_ext = os.path.basename(filepath)
    # Split the filename and extension, and return just the filename
    filename_without_ext = os.path.splitext(filename_with_ext)[0]
    return filename_without_ext

  '''
  Creates a chapters file for the audiobook.
  '''
  def create_chapters_file(self, numberSeparator=''):
    if self.directory == '':
      self.directory = os.getcwd()

    # List all MP3 files
    files_list = [f for f in os.listdir(self.directory) if f.endswith('.mp3')]
    files_list.sort()

    rawChapters = list()
    currentTimestamp = 0
    for file in files_list:
      title = self.get_filename_without_extension(file)
      if numberSeparator != '':
        title = numberSeparator.join(title.split(numberSeparator)[1:])

      filepath = os.path.join(self.directory, file)
      audioLength = self.get_duration(filepath)
      time = str(datetime.timedelta(seconds=currentTimestamp)) + '.000'
      rawChapters.append(time + ' ' + title)
      currentTimestamp = int(currentTimestamp + audioLength)

    chapters_filepath = os.path.join(self.directory, 'chapters.txt')
    with open(chapters_filepath, 'w') as chaptersFile:
      for chapter in rawChapters:
        chaptersFile.write(chapter + "\n")
    return chapters_filepath

  '''
  Retrieves the duration of the audio file in seconds using ffprobe.
  '''
  def get_duration(self, filename):
    result = subprocess.check_output(f'ffprobe -v error -show_format -of json "{filename}"', shell=True).decode()
    fields = json.loads(result)['format']
    return float(fields['duration'])


  '''
  Retrieves the bitrate of the audio file in kilobits per second (kbps) using ffprobe.
  '''
  def get_bitrate(self, filename):
    result = subprocess.check_output(f'ffprobe -v error -show_format -of json "{filename}"', shell=True).decode()
    fields = json.loads(result)['format']

    if 'bit_rate' not in fields:
      return 128
    bitrate = int(fields['bit_rate']) // 1000
    return bitrate

  '''
  Retrieves the most common bitrate among the MP3 files in the directory.
  '''
  def get_common_bitrate(self):
    mp3_files = sorted([os.path.join(self.directory, f) for f in os.listdir(self.directory) if f.endswith('.mp3')])
    bitrates = [self.get_bitrate(file) for file in mp3_files]
    print("Detected bitrates:", bitrates)
    most_common_bitrate = Counter(bitrates).most_common(1)[0][0]
    print(f"Most common bitrate: {most_common_bitrate}k\n")
    return most_common_bitrate

  '''
  Extracts the title and author of the audiobook from the directory name. The directory name
  should conform to the pattern '{TitleOfBook}_{AuthorName}' in order for the title and author
  to be extracted correctly. Each word in the title and author's name should be capitalized.
  '''
  def extract_book_info_from_directory(self, directory_name):
    # Extracting the last part of the directory name
    name_part = directory_name.split('/')[-1]

    # Separating title and author based on underscore
    parts = name_part.split('_')

    # Function to add space before capital letters and strip leading spaces
    def add_spaces(s):
      return re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', s).strip()

    # Enhanced function to handle titles like '2001ASpaceOdyssey'
    def format_title(title):
      title_with_spaces = add_spaces(title)
      # Special handling for cases like '2001A' to '2001 A'
      return re.sub(r'(\d+)([A-Z])', r'\1 \2', title_with_spaces)

    # Extracting title and author, considering cases with and without author
    title = format_title(parts[0]) if parts[0] else ''
    author = add_spaces(parts[1]) if len(parts) > 1 else ''

    return title, author

  '''
  Extracts the title of the audiobook from the directory name. The directory name
  should conform to the pattern '{TitleOfBook}_{AuthorName}' in order for the title to be
  extracted correctly. Each word in the title should be capitalized. For example,
  'TomSawyer_MarkTwain' would yield 'Tom Sawyer'.
  '''
  def extract_title(self):
    title, _ = self.extract_book_info_from_directory(self.directory)
    return title

  '''
  Extracts the author of the audiobook from the directory name. The directory name
  should conform to the pattern '{TitleOfBook}_{AuthorName}' in order for the author to be
  extracted correctly. Each word in the author's name should be capitalized. For example,
  'TomSawyer_MarkTwain' would yield 'Mark Twain'.
  '''
  def extract_author(self):
    _, author = self.extract_book_info_from_directory(self.directory)
    return author

  '''
  Searches for a cover image file (JPEG or PNG) in the directory. If found, the path to the
  cover image file is returned. If not found, an empty string is returned.
  The cover image file should be named 'cover.jpg' or 'cover.png' for it to be found.
  '''
  def find_cover_image(self):
    # Define the patterns for the file names
    patterns = ['cover.jpg', 'cover.png']

    # Search for files in the specified directory
    for pattern in patterns:
      file_list = glob.glob(os.path.join(self.directory, pattern))
      if file_list:
        return file_list[0]  # Return first match
    return ''

  '''
  Creates a file list containing the paths of the MP3 files in the directory.
  The file list is used as input to ffmpeg when binding the MP3 files into an M4B file.
  The file list is sorted alphabetically by filename.  This is important because the
  order of the files in the file list determines the order of the chapters in the M4B file.
  So the Chpter 1 MP3 file should be named '01 - Chapter Title.mp3' then '02 - Chapter Title.mp3'
  and so on. Don't forget to use the leading zero for single digit chapter numbers so that the
  files will be sorted correctly.
  '''
  def create_file_list(self):
    mp3_files = sorted([f for f in os.listdir(self.directory) if f.endswith('.mp3')])
      
    file_list_path = os.path.join(self.directory, "file_list.txt")
    if not os.path.exists(file_list_path):
      print(f"Creating file list {file_list_path} ...")
      with open(file_list_path, 'w') as file:
        for mp3_file in mp3_files:
          file.write(f"file '{mp3_file}'\n")
    return file_list_path

  def merge(self):
    # Combine MP3 files into a single M4B file using ffmpeg
    print("Combining MP3 files into a single M4B file using ffmpeg ...")
    
    if self.image != '' and os.path.exists(self.image):
      ffmpeg_cmd = [
        'ffmpeg',
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', self.create_file_list(),
        '-i', self.image,
        '-map', '0:a',
        '-fps_mode:a', 'drop',
        '-map', '1:v',
        '-c:a', f'{self.encoder}',
        '-c:v', 'copy',
        '-disposition:v:0', 
        'attached_pic',
        '-metadata', f"title={self.title}",
        '-metadata', f"album={self.title}",        
        '-metadata', f"authors={self.author}",        
        '-metadata', f"artist={self.author}",        
        '-metadata', f"genre=Audiobooks",        
        '-b:a', f'{self.bitrate()}k',
        '-threads','0',
        f'{os.path.join(self.directory, os.path.basename(self.directory))}.m4b'
      ]
    else:
      ffmpeg_cmd = [
        'ffmpeg',
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', self.create_file_list(),
        '-map', '0:a',
        '-fps_mode:a', 'drop',
        '-c:a', f'{self.encoder}',
        '-metadata', f"title={self.title}",
        '-metadata', f"album={self.title}",        
        '-metadata', f"authors={self.author}",        
        '-metadata', f"artist={self.author}",        
        '-metadata', f"genre=Audiobooks",    
        '-b:a', f'{self.bitrate()}k',
        '-threads','0',
        f'{os.path.join(self.directory, os.path.basename(self.directory))}.m4b'
      ]    
    subprocess.run(ffmpeg_cmd)

  '''
  Adds the FFMETADATA1 metadata to the M4B file. This method assumes the  metadata 
  is stored in a file named ffmetadata.txt in the source directory.
  '''
  def add_meta(self):  
    print("Adding metadata to the M4B file...\n")
    ffmpeg_cmd = ['ffmpeg', 
                  '-y', 
                  '-i', f'{os.path.join(self.directory, os.path.basename(self.directory))}.m4b',
                  '-i', self.meta_filepath, 
                  '-map_metadata', '1', 
                  '-metadata', f"title={self.title}",
                  '-metadata', f"album={self.title}",        
                  '-metadata', f"authors={self.author}",        
                  '-metadata', f"artist={self.author}",        
                  '-metadata', f"genre=Audiobooks",     
                  '-codec','copy',
                  os.path.join(self.directory,f'{self.title} - {self.author}.m4b')]
    subprocess.run(ffmpeg_cmd)



#%%
# function to determine if we are runnign in ipython notebook
def is_notebook() -> bool:
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter

'''
The code below is for running the program from the command line.
'''
if __name__ == "__main__":

  # command line arguments
  parser = argparse.ArgumentParser(description='Builds an M4B audiobook from a directory of MP3 files.')
  parser.add_argument('-d','--directory',
              default='.',
              help="The directory path containing the MP3 files to be concatenated into an M4B file. Defaults to the current directory.\n \
               The directory name will be used as the output file name if one is nor provided.\n \
               The directory can contain the Title of the book followed by an underscore and then the Author's name. \n \
               For example if the directory name was 'TomSawyer_MarkTwain', the output file would be named 'TomSawyer_MarkTwain.m4b', \n \
               the metadata Title would equal 'Tom Sawyer', and Author would be 'Mark Twain'.")

  parser.add_argument('-t', '--title',
             action='store',
             type=str,
             default='',
             help="The title of the audio book.  If not provided, the title will be extracted from the directory name. \n\
               The directory name shall conform to the pattern '{Title}_{Author}'.")

  parser.add_argument('-a', '--author',
            action='store',
            type=str,
            default='',
            help="The author of the book.  If not provided, the author's name will be extracted from the directory name. \n\
              The directory name shall conform to the pattern '{Title}_{Author}'.")

  parser.add_argument('-i', '--image',
            action='store',
            type=str,
            default='',
            help="The path to the cover art of the book.  If not provided, this software will look for cover.jpg or cover.png in the source directory, \n \
              and if found this image wil be atached to the m4b ourput file. If nott found and not specified here, no image will be included'.")

  parser.add_argument('-e', '--encoder',
            action='store',
            type=str,
            default='aac',
            help='The audio encoder to use.',
            choices=['aac', 'alac', 'flac', 'libmp3lame', 'mpeg4'])

  parser.add_argument('-e', '--encoder',
            action='store',
            type=str,
            default='aac',
            help='The audio encoder to use.',
            choices=['aac', 'alac', 'flac', 'libmp3lame', 'mpeg4'])

  parser.add_argument('-b', '--bitrate',
            action='store',
            type=int,
            default=0,
            help='The bitrate to use for the output file.  If not provided, the most common bitrate among the MP3 files in the directory will be used.')

  if is_notebook():
    # for running in a notebook or vscode
    a = parser.parse_args('')
    directory = 'mp3s/TheEggandOtherStories_AndyWeir' # change this line to the directory containing the mp3 files
  else:
    a = parser.parse_args()  
    directory = a.directory  
    
  converter = PyAudiobookBinder(directory, a.title, a.author, a.image, a.encoder, a.bitrate)
  converter.combine_mp3_to_m4b()
  
# %%
      
