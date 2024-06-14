import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pytube import YouTube
from pytube.exceptions import VideoUnavailable
from PIL import Image, ImageTk
import io
import requests
import os
import threading
import time
import ssl
import certifi
from languages import languages
from pydantic import BaseModel, ValidationError, field_validator
from mutagen.easyid3 import EasyID3
import ffmpeg
import sys

# Ensure that the certifi certificates are used
os.environ['SSL_CERT_FILE'] = certifi.where()

# Resolve resource paths
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Pydantic Model for Video URL
class VideoInfo(BaseModel):
    url: str

    @field_validator('url')
    def url_must_be_valid(cls, v):
        if 'youtube.com' not in v:
            raise ValueError('Must be a valid YouTube URL')
        return v

class YouTubeDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Video Downloader")
        self.geometry("600x700")
        self.configure(bg="#2b2b2b")

        self.languages = languages
        self.current_language = self.load_saved_language() or "English"

        # Language Selection
        self.language_var = tk.StringVar(value=self.current_language)
        self.language_menu = tk.OptionMenu(self, self.language_var, *self.languages.keys(), command=self.save_language)
        self.language_menu.place(relx=1.0, rely=0, anchor='ne')

        # Title Label
        self.title_label = tk.Label(self, text=self.languages[self.current_language]["title"], font=("Helvetica", 18, "bold"), bg="#2b2b2b", fg="white")
        self.title_label.pack(pady=20)

        # URL Frame
        self.url_frame = tk.Frame(self, bg="#2b2b2b")
        self.url_frame.pack(pady=10)

        self.url_label = tk.Label(self.url_frame, text=self.languages[self.current_language]["url_label"], font=("Helvetica", 12), bg="#2b2b2b", fg="white")
        self.url_label.pack(side=tk.LEFT, padx=10)

        self.url_entry = tk.Entry(self.url_frame, width=40, font=("Helvetica", 12))
        self.url_entry.pack(side=tk.LEFT, padx=10)
        self.url_entry.bind("<KeyRelease>", self.delayed_fetch)
        self.url_entry.bind("<Control-a>", self.select_all)
        self.url_entry.bind("<Control-A>", self.select_all)  # For uppercase 'A'

        # Status Label
        self.status_label = tk.Label(self, text=self.languages[self.current_language]["status_label"], font=("Helvetica", 10), bg="#2b2b2b", fg="red")
        self.status_label.pack(pady=10)

        # Thumbnail Label
        self.thumbnail_label = tk.Label(self, bg="#2b2b2b")
        self.thumbnail_label.pack(pady=10)

        # Format Frame
        self.format_frame = tk.Frame(self, bg="#2b2b2b")
        self.format_frame.pack(pady=10)

        self.format_label = tk.Label(self.format_frame, text=self.languages[self.current_language]["format_label"], font=("Helvetica", 12), bg="#2b2b2b", fg="white")
        self.format_label.pack(side=tk.LEFT, padx=10)

        self.format_var = tk.StringVar(value="mp4")
        self.mp4_radio = tk.Radiobutton(self.format_frame, text="MP4", variable=self.format_var, value="mp4", font=("Helvetica", 12), bg="#2b2b2b", fg="white", selectcolor="#2b2b2b")
        self.mp3_radio = tk.Radiobutton(self.format_frame, text="MP3", variable=self.format_var, value="mp3", font=("Helvetica", 12), bg="#2b2b2b", fg="white", selectcolor="#2b2b2b")
        self.mp4_radio.pack(side=tk.LEFT, padx=10)
        self.mp3_radio.pack(side=tk.LEFT, padx=10)

        # Location Button
        self.location_button = tk.Button(self, text=self.languages[self.current_language]["location_button"], font=("Helvetica", 12), bg="#4CAF50", fg="white", command=self.select_location)
        self.location_button.pack(pady=10)

        # Download Button
        self.download_button = tk.Button(self, text=self.languages[self.current_language]["download_button"], font=("Helvetica", 12), bg="#008CBA", fg="white", command=self.start_download_thread)
        self.download_button.pack(pady=10)

        # Download from File Button
        self.file_download_button = tk.Button(self, text=self.languages[self.current_language]["file_download_button"], font=("Helvetica", 12), bg="#f44336", fg="white", command=self.start_file_download_thread)
        self.file_download_button.pack(pady=10)

        # Progress Bar
        self.progress = ttk.Progressbar(self, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=20)

        # Additional Info Frame
        self.info_frame = tk.Frame(self, bg="#2b2b2b")
        self.info_frame.pack(pady=10)

        self.speed_label = tk.Label(self.info_frame, text=self.languages[self.current_language]["speed_label"], font=("Helvetica", 12), bg="#2b2b2b", fg="white")
        self.speed_label.pack(side=tk.LEFT, padx=10)

        self.num_videos_label = tk.Label(self.info_frame, text=self.languages[self.current_language]["num_videos_label"], font=("Helvetica", 12), bg="#2b2b2b", fg="white")
        self.num_videos_label.pack(side=tk.LEFT, padx=10)

        self.download_location = ""
        self.video = None
        self.fetch_job = None
        self.start_time = None
        self.total_videos = 0
        self.current_video = 0

    def change_language(self, lang):
        self.current_language = lang
        self.update_texts()
        
    def save_language(self, lang):
        self.current_language = lang
        self.update_texts()
        self.save_language_preference(lang)

    def load_saved_language(self):
        try:
            with open(resource_path("language_preference.txt"), "r") as file:
                return file.read().strip()
        except FileNotFoundError:
            return None

    def save_language_preference(self, lang):
        with open(resource_path("language_preference.txt"), "w") as file:
            file.write(lang)
    

    def update_texts(self):
        self.title(self.languages[self.current_language]["title"])
        self.title_label.config(text=self.languages[self.current_language]["title"])
        self.url_label.config(text=self.languages[self.current_language]["url_label"])
        self.format_label.config(text=self.languages[self.current_language]["format_label"])
        self.location_button.config(text=self.languages[self.current_language]["location_button"])
        self.download_button.config(text=self.languages[self.current_language]["download_button"])
        self.file_download_button.config(text=self.languages[self.current_language]["file_download_button"])
        self.speed_label.config(text=self.languages[self.current_language]["speed_label"])
        self.num_videos_label.config(text=self.languages[self.current_language]["num_videos_label"])
        self.status_label.config(text=self.languages[self.current_language]["status_label"])

    def select_all(self, event):
        self.url_entry.select_range(0, tk.END)
        self.url_entry.icursor(tk.END)
        return 'break'

    def delayed_fetch(self, event):
        if self.fetch_job is not None:
            self.after_cancel(self.fetch_job)
        self.fetch_job = self.after(1000, self.fetch_video)

    def fetch_video(self):
        url = self.url_entry.get()
        if not url:
            self.status_label.config(text=self.languages[self.current_language]["enter_url"], fg="red")
            return

        try:
            video_info = VideoInfo(url=url)
            self.video = YouTube(url, on_progress_callback=self.progress_callback)
            response = requests.get(self.video.thumbnail_url)
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            image = image.resize((320, 180), Image.Resampling.LANCZOS)
            thumbnail = ImageTk.PhotoImage(image)
            self.thumbnail_label.config(image=thumbnail)
            self.thumbnail_label.image = thumbnail
            self.status_label.config(text=self.languages[self.current_language]["fetch_success"], fg="green")
        except ValidationError as e:
            self.thumbnail_label.config(image='')
            self.status_label.config(text=self.languages[self.current_language]["invalid_url"], fg="red")
        except VideoUnavailable:
            self.thumbnail_label.config(image='')
            self.status_label.config(text=self.languages[self.current_language]["video_unavailable"], fg="red")
        except Exception as e:
            self.thumbnail_label.config(image='')
            self.status_label.config(text=f"{self.languages[self.current_language]['fetch_fail']}{e}", fg="red")

    def select_location(self):
        self.download_location = filedialog.askdirectory()
        if self.download_location:
            self.status_label.config(text=f"Download location set to: {self.download_location}", fg="green")

    def get_download_location(self):
        return self.download_location if self.download_location else os.path.expanduser("~/Downloads")

    def start_download_thread(self):
        self.total_videos = 1
        self.current_video = 0
        self.num_videos_label.config(text=f"Videos: {self.current_video}/{self.total_videos}")
        thread = threading.Thread(target=self.download_video)
        thread.start()

    def start_file_download_thread(self):
        thread = threading.Thread(target=self.download_from_file)
        thread.start()

    def download_video(self):
        if not self.video:
            self.status_label.config(text=self.languages[self.current_language]["no_video"], fg="red")
            return

        download_location = self.get_download_location()

        try:
            format_choice = self.format_var.get()
            if format_choice == "mp4":
                stream = self.video.streams.get_highest_resolution()
                output_path = stream.download(output_path=download_location)
                self.status_label.config(text=f"Downloaded video to: {output_path}", fg="green")
            elif format_choice == "mp3":
                audio_stream = self.video.streams.filter(only_audio=True).first()
                output_filename = f"{self.video.title}.mp3"
                output_path = os.path.join(download_location, output_filename)

                # Download and convert using ffmpeg-python
                (
                    ffmpeg
                    .input(audio_stream.url)
                    .output(output_path, format='mp3', acodec='libmp3lame', ab='320k', ar='44100')
                    .run()
                )

                self.tag_audio(output_path)

            self.progress["value"] = 100
            self.update_idletasks()
            self.speed_label.config(text="Speed: 0 MB/s")

        except VideoUnavailable:
            self.status_label.config(text="This video is unavailable", fg="red")
        except Exception as e:
            self.status_label.config(text=f"Failed to download: {e}", fg="red")


    def tag_audio(self, output_path):
        try:
            audio_file = EasyID3(output_path)
            audio_file["title"] = self.video.title
            audio_file["artist"] = self.video.author
            audio_file["album"] = self.video.title
            audio_file["genre"] = "Podcast"
            audio_file.save()
            self.status_label.config(text=f"Downloaded and tagged audio to: {output_path}", fg="green")
        except Exception as e:
            self.status_label.config(text=f"Audio downloaded but tagging failed: {e}", fg="red")

    def progress_callback(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = (bytes_downloaded / total_size) * 100

        elapsed_time = time.time() - self.start_time
        download_speed = bytes_downloaded / (1024 * 1024) / elapsed_time if elapsed_time > 0 else 0

        self.progress["value"] = percentage_of_completion
        self.speed_label.config(text=f"Speed: {download_speed:.2f} MB/s")
        self.update_idletasks()

    def download_from_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not file_path:
            self.status_label.config(text="No file selected", fg="red")
            return

        download_location = self.get_download_location()

        try:
            with open(file_path, 'r') as file:
                urls = file.readlines()
            self.total_videos = len(urls)
            self.current_video = 0

            for idx, url in enumerate(urls):
                url = url.strip()
                if url:
                    try:
                        self.url_entry.delete(0, tk.END)
                        self.url_entry.insert(0, url)
                        self.fetch_video()

                        self.video = YouTube(url, on_progress_callback=self.progress_callback)
                        format_choice = self.format_var.get()
                        if format_choice == "mp4":
                            stream = self.video.streams.get_highest_resolution()
                            output_path = stream.download(output_path=download_location)
                            self.status_label.config(text=f"Downloaded video to: {output_path}", fg="green")
                        elif format_choice == "mp3":
                            audio_stream = self.video.streams.filter(only_audio=True).first()
                            output_filename = f"{self.video.title}.mp3"
                            output_path = os.path.join(download_location, output_filename)

                            # Download and convert using ffmpeg-python
                            (
                                ffmpeg
                                .input(audio_stream.url)
                                .output(output_path, format='mp3', acodec='libmp3lame', ab='320k', ar='44100')
                                .run()
                            )

                            self.tag_audio(output_path)

                        self.progress["value"] = 100
                        self.update_idletasks()
                        self.speed_label.config(text="Speed: 0 MB/s")
                        
                    except VideoUnavailable:
                        self.status_label.config(text=f"Video unavailable: {url}", fg="red")
                    except Exception as e:
                        self.status_label.config(text=f"Failed to download: {e}", fg="red")

            self.status_label.config(text="All downloads completed", fg="green")
            self.speed_label.config(text="Speed: 0 MB/s")
            self.num_videos_label.config(text="Videos: 0/0")
        except Exception as e:
            self.status_label.config(text=f"Error reading file: {e}", fg="red")

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()