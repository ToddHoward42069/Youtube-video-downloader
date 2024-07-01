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
import sys
import ffmpeg_script

# Ensure that the certifi certificates are used
os.environ["SSL_CERT_FILE"] = certifi.where()

# Resolve resource paths (if needed)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class YouTubeDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Video Downloader")
        self.configure(bg="#2b2b2b")
        # Window Size
        self.minsize(800, 600)

        # Version Number
        self.version = "1.3.0"

        # Load Languages
        self.languages = languages
        self.current_language = self.load_saved_language() or "English"

        # --- UI Elements ---
        self.create_widgets()

        # Initial Settings
        self.download_location = ""
        self.video = None
        self.fetch_job = None
        self.start_time = None
        self.total_videos = 0
        self.current_video = 0
        self.last_downloaded_path = None
        self.downloaded_files = []
        self.download_thread = None

    def create_widgets(self):
        # --- Top Frame (Title, Version, Language) ---
        top_frame = tk.Frame(self, bg="#2b2b2b")
        top_frame.pack(pady=20)

        self.title_label = tk.Label(
            top_frame,
            text=self.languages[self.current_language]["title"],
            font=("Helvetica", 24, "bold"),
            bg="#2b2b2b",
            fg="white",
        )
        self.title_label.pack(side=tk.LEFT, padx=10)

        self.version_label = tk.Label(
            top_frame,
            text=f"v.{self.version}",
            font=("Helvetica", 12),
            bg="#2b2b2b",
            fg="white",
        )
        self.version_label.pack(side=tk.RIGHT, padx=10)

        self.language_var = tk.StringVar(value=self.current_language)
        self.language_menu = tk.OptionMenu(
            top_frame,
            self.language_var,
            *self.languages.keys(),
            command=self.change_language,
        )
        self.language_menu.config(font=("Helvetica", 12))
        self.language_menu.pack(side=tk.RIGHT, padx=10)

        # --- URL and Fetch Button Frame ---
        url_frame = tk.Frame(self, bg="#2b2b2b")
        url_frame.pack(pady=10)

        self.url_label = tk.Label(
            url_frame,
            text=self.languages[self.current_language]["url_label"],
            font=("Helvetica", 14),
            bg="#2b2b2b",
            fg="white",
        )
        self.url_label.pack(side=tk.LEFT, padx=10)

        self.url_entry = tk.Entry(url_frame, width=60, font=("Helvetica", 14))
        self.url_entry.pack(side=tk.LEFT, padx=10)
        self.url_entry.bind("<KeyRelease>", self.delayed_fetch)
        self.url_entry.bind("<Control-a>", self.select_all)
        self.url_entry.bind("<Control-A>", self.select_all)

        # --- Thumbnail and Options Frame ---
        thumbnail_options_frame = tk.Frame(self, bg="#2b2b2b")
        thumbnail_options_frame.pack(pady=20)

        # Thumbnail
        self.thumbnail_label = tk.Label(
            thumbnail_options_frame, bg="#2b2b2b"
        )
        self.thumbnail_label.pack(side=tk.LEFT, padx=20)

        # --- Download Options Frame ---
        options_frame = tk.Frame(thumbnail_options_frame, bg="#2b2b2b")
        options_frame.pack(side=tk.LEFT, padx=20)

        # Format Options
        self.format_label = tk.Label(
            options_frame,
            text=self.languages[self.current_language]["format_label"],
            font=("Helvetica", 14),
            bg="#2b2b2b",
            fg="white",
        )
        self.format_label.pack(pady=10)

        self.format_var = tk.StringVar(value="mp4")
        self.mp4_radio = tk.Radiobutton(
            options_frame,
            text="MP4",
            variable=self.format_var,
            value="mp4",
            font=("Helvetica", 12),
            bg="#2b2b2b",
            fg="white",
            selectcolor="#2b2b2b",
        )
        self.mp4_radio.pack(anchor="w")

        self.mp3_radio = tk.Radiobutton(
            options_frame,
            text="MP3",
            variable=self.format_var,
            value="mp3",
            font=("Helvetica", 12),
            bg="#2b2b2b",
            fg="white",
            selectcolor="#2b2b2b",
        )
        self.mp3_radio.pack(anchor="w")

        # Tag After Download Checkbox
        self.tag_after_download_var = tk.BooleanVar(value=False)
        self.tag_after_download_checkbox = tk.Checkbutton(
            options_frame,
            text=self.languages[self.current_language]["tag_checkbox_text"],
            variable=self.tag_after_download_var,
            bg="#2b2b2b",
            fg="white",
            selectcolor="#2b2b2b",
            font=("Helvetica", 12),  # Larger font
        )
        self.tag_after_download_checkbox.pack(pady=10, anchor="w")

        # --- Download Related Buttons Frame ---
        download_button_frame = tk.Frame(self, bg="#2b2b2b")
        download_button_frame.pack(pady=10)

        # Location Button
        self.location_button = tk.Button(
            download_button_frame,
            text=self.languages[self.current_language]["location_button"],
            font=("Helvetica", 14),
            bg="#4CAF50",
            fg="white",
            command=self.select_location,
        )
        self.location_button.pack(side=tk.LEFT, padx=10)

        # Download Button
        self.download_button = tk.Button(
            download_button_frame,
            text=self.languages[self.current_language]["download_button"],
            font=("Helvetica", 14),
            bg="#008CBA",
            fg="white",
            command=self.start_download_thread,
        )
        self.download_button.pack(side=tk.LEFT, padx=10)

        # --- File Download and Tagging Buttons Frame ---
        file_tag_button_frame = tk.Frame(self, bg="#2b2b2b")
        file_tag_button_frame.pack(pady=10)

        # File Download Button
        self.file_download_button = tk.Button(
            file_tag_button_frame,
            text=self.languages[self.current_language]["file_download_button"],
            font=("Helvetica", 14),
            bg="#f44336",
            fg="white",
            command=self.start_file_download_thread,
        )
        self.file_download_button.pack(side=tk.LEFT, padx=10)

        # Tag List Button
        self.tag_list_button = tk.Button(
            file_tag_button_frame,
            text=self.languages[self.current_language]["tag_list_button"],
            font=("Helvetica", 14),
            bg="#f44336",
            fg="white",
            command=self.tag_files_in_directory,
        )
        self.tag_list_button.pack(side=tk.LEFT, padx=10)

        # --- Progress and Status Frame ---
        progress_frame = tk.Frame(self, bg="#2b2b2b")
        progress_frame.pack(pady=20)

        self.progress = ttk.Progressbar(
            progress_frame, orient="horizontal", length=600, mode="determinate"
        )
        self.progress.pack(pady=10)

        self.status_label = tk.Label(
            progress_frame,
            text=self.languages[self.current_language]["status_label"],
            font=("Helvetica", 12),
            bg="#2b2b2b",
            fg="red",
        )
        self.status_label.pack()

        # --- Info Frame ---
        info_frame = tk.Frame(self, bg="#2b2b2b")
        info_frame.pack()

        self.speed_label = tk.Label(
            info_frame,
            text=self.languages[self.current_language]["speed_label"],
            font=("Helvetica", 12),
            bg="#2b2b2b",
            fg="white",
        )
        self.speed_label.pack(side=tk.LEFT, padx=20)

        self.num_videos_label = tk.Label(
            info_frame,
            text=self.languages[self.current_language]["num_videos_label"],
            font=("Helvetica", 12),
            bg="#2b2b2b",
            fg="white",
        )
        self.num_videos_label.pack(side=tk.LEFT, padx=20)

    def change_language(self, lang):
        self.current_language = lang
        self.update_texts()
        self.save_language_preference(lang)

    def load_saved_language(self):
        try:
            with open("language_preference.txt", "r") as file:
                return file.read().strip()
        except FileNotFoundError:
            return "English"

    def save_language_preference(self, lang):
        with open("language_preference.txt", "w") as file:
            file.write(lang)

    def update_texts(self):
        self.title(self.languages[self.current_language]["title"])
        self.title_label.config(text=self.languages[self.current_language]["title"])
        self.url_label.config(text=self.languages[self.current_language]["url_label"])
        self.format_label.config(
            text=self.languages[self.current_language]["format_label"]
        )
        self.location_button.config(
            text=self.languages[self.current_language]["location_button"]
        )
        self.download_button.config(
            text=self.languages[self.current_language]["download_button"]
        )
        self.file_download_button.config(
            text=self.languages[self.current_language]["file_download_button"]
        )
        self.tag_list_button.config(
            text=self.languages[self.current_language]["tag_list_button"]
        )
        self.speed_label.config(
            text=self.languages[self.current_language]["speed_label"]
        )
        self.num_videos_label.config(
            text=self.languages[self.current_language]["num_videos_label"]
        )
        self.status_label.config(
            text=self.languages[self.current_language]["status_label"]
        )
        self.tag_after_download_checkbox.config(
            text=self.languages[self.current_language]["tag_checkbox_text"]
        )

    def select_all(self, event):
        self.url_entry.select_range(0, tk.END)
        self.url_entry.icursor(tk.END)
        return "break"

    def delayed_fetch(self, event):
        if self.fetch_job is not None:
            self.after_cancel(self.fetch_job)
        self.fetch_job = self.after(1000, self.fetch_video)

    def fetch_video(self):
        url = self.url_entry.get()
        if not url:
            self.status_label.config(
                text=self.languages[self.current_language]["enter_url"], fg="red"
            )
            return

        try:
            self.video = YouTube(
                url, on_progress_callback=self.progress_callback
            )
            self.show_thumbnail(self.video.thumbnail_url)
            self.status_label.config(
                text=self.languages[self.current_language]["fetch_success"],
                fg="green",
            )
        except VideoUnavailable:
            self.thumbnail_label.config(image="")
            self.status_label.config(
                text=self.languages[self.current_language]["video_unavailable"],
                fg="red",
            )
        except Exception as e:
            self.thumbnail_label.config(image="")
            self.status_label.config(
                text=f"{self.languages[self.current_language]['fetch_fail']}{e}",
                fg="red",
            )

    def show_thumbnail(self, thumbnail_url):
        response = requests.get(thumbnail_url)
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))

        # Resize while maintaining aspect ratio
        image.thumbnail((320, 240))  # Adjust maximum size as needed
        thumbnail = ImageTk.PhotoImage(image)
        self.thumbnail_label.config(image=thumbnail)
        self.thumbnail_label.image = thumbnail

    def select_location(self):
        self.download_location = filedialog.askdirectory()
        if self.download_location:
            self.status_label.config(
                text=f"Download location set to: {self.download_location}",
                fg="green",
            )

    def get_download_location(self):
        return (
            self.download_location
            if self.download_location
            else os.path.expanduser("~/Downloads")
        )

    def start_download_thread(self):
        if self.download_thread and self.download_thread.is_alive():
            return

        self.total_videos = 1
        self.current_video = 0
        self.num_videos_label.config(
            text=f"Videos: {self.current_video}/{self.total_videos}"
        )
        self.download_thread = threading.Thread(target=self.download_video)
        self.download_thread.start()

    def start_file_download_thread(self):
        if self.download_thread and self.download_thread.is_alive():
            return
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not file_path:
            self.status_label.config(
                text=self.languages[self.current_language]["no_file_selected"],
                fg="red",
            )
            return

        self.download_thread = threading.Thread(
            target=self.download_videos_from_file, args=(file_path,)
        )
        self.download_thread.start()

    def download_videos_from_file(self, file_path):
        download_location = self.get_download_location()
        try:
            with open(file_path, "r") as file:
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
                        self.video = YouTube(
                            url, on_progress_callback=self.progress_callback
                        )
                        self.download_single_video(download_location)

                        # Update progress information
                        self.current_video = idx + 1
                        self.num_videos_label.config(
                            text=f"Videos: {self.current_video}/{self.total_videos}"
                        )
                        self.progress["value"] = (
                            self.current_video / self.total_videos
                        ) * 100
                        self.update_idletasks()

                    except VideoUnavailable:
                        self.status_label.config(
                            text=f"Video unavailable: {url}", fg="red"
                        )
                    except Exception as e:
                        self.status_label.config(
                            text=f"Failed to download: {e}", fg="red"
                        )
            self.status_label.config(
                text=self.languages[self.current_language]["all_downloads_complete"],
                fg="green",
            )
            self.speed_label.config(text="Speed: 0 MB/s")
        except Exception as e:
            self.status_label.config(
                text=f"{self.languages[self.current_language]['error_reading_file']}{e}",
                fg="red",
            )

    def download_video(self):
        if not self.video:
            self.status_label.config(
                text=self.languages[self.current_language]["no_video"], fg="red"
            )
            return

        download_location = self.get_download_location()

        # Create and start the download thread
        self.download_thread = threading.Thread(
            target=self.download_single_video, args=(download_location,)
        )
        self.download_thread.start()

    def download_single_video(self, download_location):
        try:
            self.start_time = time.time()
            format_choice = self.format_var.get()
            if format_choice == "mp4":
                stream = self.video.streams.get_highest_resolution()
                output_path = stream.download(output_path=download_location)
            elif format_choice == "mp3":
                audio_stream = self.video.streams.filter(only_audio=True).first()
                output_filename = f"{self.video.title}.mp3"
                output_path = os.path.join(download_location, output_filename)
                audio_stream.download(
                    filename=output_filename, output_path=download_location
                )
                if self.tag_after_download_var.get():
                    self.tag_audio(output_path)
                self.downloaded_files.append(output_path)

            self.last_downloaded_path = output_path
            self.status_label.config(
                text=f"Downloaded to: {output_path}", fg="green"
            )

            # Update GUI elements
            self.progress["value"] = 100
            self.speed_label.config(text="Speed: 0 MB/s")
            self.update_idletasks()

        except VideoUnavailable:
            self.status_label.config(
                text=self.languages[self.current_language]["video_unavailable"],
                fg="red",
            )
        except Exception as e:
            self.status_label.config(
                text=f"Failed to download: {e}", fg="red"
            )

    def tag_audio(self, output_path):
        if output_path.endswith(".mp3"):
            try:
                ffmpeg_script.add_bitrate_samplerate(input_file=output_path)
                self.status_label.config(
                    text=f"Audio tagged: {output_path}", fg="green"
                )
            except Exception as e:
                self.status_label.config(
                    text=f"Audio tagging failed: {e}", fg="red"
                )
        else:
            self.status_label.config(
                text=f"Tagging is only supported for MP3 files", fg="red"
            )

    def progress_callback(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize

        if bytes_remaining is None:
            bytes_downloaded = 0
            percentage_of_completion = 0
        else:
            bytes_downloaded = total_size - bytes_remaining
            percentage_of_completion = (bytes_downloaded / total_size) * 100

        if self.start_time is None:
            self.start_time = time.time()

        elapsed_time = time.time() - self.start_time
        download_speed_bps = (
            bytes_downloaded / elapsed_time if elapsed_time > 0 else 0
        )

        if download_speed_bps >= 1024 * 1024:
            download_speed = download_speed_bps / (1024 * 1024)
            speed_unit = "MB/s"
        else:
            download_speed = download_speed_bps / 1024
            speed_unit = "KB/s"

        self.progress["value"] = percentage_of_completion
        self.speed_label.config(text=f"Speed: {download_speed:.2f} {speed_unit}")
        self.update_idletasks()

    def tag_files_in_directory(self):
        directory = filedialog.askdirectory()
        if not directory:
            self.status_label.config(
                text=self.languages[self.current_language]["no_file_selected"],
                fg="red",
            )
            return

        for filename in os.listdir(directory):
            if filename.endswith(".mp3"):
                file_path = os.path.join(directory, filename)
                try:
                    ffmpeg_script.add_bitrate_samplerate(input_file=file_path)
                    self.status_label.config(
                        text=f"Audio tagged: {file_path}", fg="green"
                    )
                except Exception as e:
                    self.status_label.config(
                        text=f"Audio tagging failed: {e}", fg="red"
                    )
        self.status_label.config(text="Tagging complete.", fg="green")


if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
