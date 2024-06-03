# setup.py
import sys
from cx_Freeze import setup, Executable
import os

# Path to the DLL file
dll_path = 'C:\\Windows\\System32\\VCRUNTIME140.dll'

build_exe_options = {
    "packages": ["os", "tkinter", "pytube", "PIL", "requests", "certifi"],
    "excludes": [],
    "include_files": [dll_path]
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Use this if you don't want a console window

setup(
    name="YouTubeDownloader",
    version="0.1",
    description="YouTube Video Downloader",
    options={"build_exe": build_exe_options},
    executables=[Executable("youtube_downloader.py", base=base)]
)
