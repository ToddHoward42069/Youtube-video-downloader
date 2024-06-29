#!/bin/zsh
pyinstaller --onefile --windowed --name "Youtube-Video-Downloader" --hidden-import "PIL._imaging" --hidden-import "PIL" --hidden-import "pytube" --hidden-import "requests" --hidden-import "certifi" --hidden-import "pydantic" --hidden-import "ffmpeg" --hidden-import "ffmpeg_python" --hidden-import "PIL._tkinter_finder" main.pyw
