# setup.py
import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["os", "tkinter", "pytube", "PIL", "requests", "certifi"],
    "excludes": [],
    "include_files": []
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
