import tkinter as tk
from tkinter import filedialog, ttk, messagebox
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
import subprocess
import shutil
import tempfile
from mutagen.easyid3 import EasyID3
import yt_dlp
import queue

# Ensure that the certifi certificates are used
os.environ["SSL_CERT_FILE"] = certifi.where()

# Resolve resource paths (if needed)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def add_bitrate_samplerate(input_file, bitrate="320k", samplerate="44100"):
    """Adds bitrate and samplerate to the input file, overwriting the original."""
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file.close()

        command = [
            "ffmpeg",
            "-avoid_negative_ts", "make_zero",
            "-i", input_file,
            "-b:a", bitrate,
            "-ar", samplerate,
            "-map_metadata", "-1",
            "-c:v", "copy",
            "-vn",  # Remove video stream if present
            "-y",
            temp_file.name,
        ]

        # Platform-specific handling for hiding the FFmpeg console window
        if sys.platform.startswith('win'):
            creationflags = subprocess.CREATE_NO_WINDOW
        else:
            creationflags = 0  # No special flags for other platforms

        subprocess.run(command, check=True, creationflags=creationflags)
        shutil.copyfile(temp_file.name, input_file)
        os.remove(temp_file.name)

        print(f"FFmpeg script executed successfully. File modified: {input_file}")

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg script failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

class YouTubeDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Video Downloader")
        self.configure(bg="#2b2b2b")
        self.minsize(800, 620)

        self.version = "1.5.0"
        self.languages = languages
        self.current_language = self.load_saved_language() or "English"

        self.create_widgets()
        self.download_location = self.get_download_location()
        self.video_info = None
        self.fetch_job = None
        self.start_time = None
        self.total_videos = 0
        self.current_video = 0
        self.last_downloaded_path = None
        self.downloaded_files = []
        self.download_thread = None
        self.tagging_progress = tk.IntVar(value=0)

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
        self.thumbnail_label = tk.Label(thumbnail_options_frame, bg="#2b2b2b")
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
            bg="#e0d74f",
            fg="white",
            command=self.tag_files_in_directory,
        )
        self.tag_list_button.pack(side=tk.LEFT, padx=10)

        # --- Rename Button ---
        self.rename_button = tk.Button(
            file_tag_button_frame,
            text="Rename M4A to MP3",
            font=("Helvetica", 14),
            bg="#9403fc",
            fg="white",
            command=self.rename_m4a_to_mp3,
        )
        self.rename_button.pack(side=tk.LEFT, padx=10)

        # --- Progress and Status Frame ---
        progress_frame = tk.Frame(self, bg="#2b2b2b")
        progress_frame.pack(pady=20)

        # Download Progress Bar
        self.download_progress_label = tk.Label(
            progress_frame,
            text=self.languages[self.current_language]["download_progressbar_label"],
            font=("Helvetica", 12),
            bg="#2b2b2b",
            fg="white",
        )
        self.download_progress_label.pack()

        self.progress = ttk.Progressbar(
            progress_frame, orient="horizontal", length=600, mode="determinate"
        )
        self.progress.pack(pady=10)

        # Tagging Progress Bar
        self.tagging_progress_label = tk.Label(
            progress_frame,
            text=self.languages[self.current_language]["tagging_progressbar_label"],
            font=("Helvetica", 12),
            bg="#2b2b2b",
            fg="white",
        )
        self.tagging_progress_label.pack()

        self.tagging_progressbar = ttk.Progressbar(
            progress_frame, orient="horizontal", length=600, mode="determinate"
        )
        self.tagging_progressbar.pack(pady=10)

        self.status_label = tk.Label(
            progress_frame,
            text=self.languages[self.current_language]["status_label"],
            font=("Helvetica", 12),
            bg="#2b2b2b",
            fg="red",
            wraplength=600
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
        # Update progress bar labels
        self.download_progress_label.config(
            text=self.languages[self.current_language]["download_progressbar_label"]
        )
        self.tagging_progress_label.config(
            text=self.languages[self.current_language]["tagging_progressbar_label"]
        )
        self.rename_button.config(
            text=self.languages[self.current_language]["rename_button"]
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
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                self.video_info = ydl.extract_info(url, download=False)

            self.show_thumbnail(self.video_info['thumbnail'])
            self.status_label.config(
                text=self.languages[self.current_language]["fetch_success"],
                fg="green",
            )
        except yt_dlp.DownloadError as e:
            self.thumbnail_label.config(image="")
            error_message = str(e).split("\n")[0]
            self.status_label.config(text=error_message, fg="red")
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

        image.thumbnail((320, 240))
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
        return os.path.expanduser("~/Downloads")

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
        download_location = self.download_location
        try:
            with open(file_path, "r", encoding='utf-8') as file:
                urls = file.readlines()
            self.total_videos = len(urls)
            self.current_video = 0

            for idx, url in enumerate(urls):
                url = url.strip()
                if url:
                    try:
                        self.url_entry.delete(0, tk.END)
                        self.url_entry.insert(0, url)
                        self.fetch_video()  # Fetch video info for the current URL

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
        if not self.video_info:  # Check video_info, not video
            self.status_label.config(
                text=self.languages[self.current_language]["no_video"], fg="red"
            )
            return

        download_location = self.download_location

        self.download_thread = threading.Thread(
            target=self.download_single_video, args=(download_location,)
        )
        self.download_thread.start()

    def download_single_video(self, download_location):
        url = self.url_entry.get()
        format_choice = self.format_var.get()

        try:
            self.start_time = time.time()

            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best' if format_choice == 'mp4' else 'ba[ext=m4a]',
                'outtmpl': os.path.join(download_location, '%(title)s.%(ext)s'),
                'progress_hooks': [self.yt_dlp_progress_hook],
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # --- Rename M4A to MP3 in a separate thread using a queue ---
            if format_choice == 'mp3':
                rename_queue = queue.Queue()

                def rename_thread(video_info): # Pass video_info to the thread
                    m4a_file = os.path.join(download_location, f"{video_info['title']}.m4a")
                    mp3_file = os.path.join(download_location, f"{video_info['title']}.mp3")

                    while not os.path.exists(m4a_file):
                        time.sleep(1)

                    os.rename(m4a_file, mp3_file)
                    self.last_downloaded_path = mp3_file
                    rename_queue.put("rename_done")

                threading.Thread(target=rename_thread, args=(self.video_info,)).start()  # Pass video_info as argument

                def check_rename_queue():
                    if not rename_queue.empty():
                        rename_queue.get()

                        # --- Update GUI and proceed with other downloads ---
                        self.downloaded_files.append(self.last_downloaded_path)

                        if self.tag_after_download_var.get():
                            self.tag_audio(self.last_downloaded_path)

                        self.status_label.config(
                            text=f"Downloaded to: {self.last_downloaded_path}",
                            fg="green"
                        )

                        self.progress["value"] = 100
                        self.speed_label.config(text="Speed: 0 MB/s")
                        self.update_idletasks()
                    else:
                        self.after(100, check_rename_queue)

                self.after(100, check_rename_queue)

            else:
                self.last_downloaded_path = os.path.join(download_location, f"{self.video_info['title']}.mp4")
                self.downloaded_files.append(self.last_downloaded_path)

                self.status_label.config(
                    text=f"Downloaded to: {self.last_downloaded_path}",
                    fg="green"
                )

                self.progress["value"] = 100
                self.speed_label.config(text="Speed: 0 MB/s")
                self.update_idletasks()

        except yt_dlp.DownloadError as e:
            error_message = str(e).split("\n")[0]
            self.status_label.config(text=error_message, fg="red")
        except Exception as e:
            self.status_label.config(
                text=f"Failed to download: {e}", fg="red"
            )

    def rename_m4a_to_mp3(self):
        directory = filedialog.askdirectory()
        if not directory:
            self.status_label.config(text="No directory selected.", fg="red")
            return

        for filename in os.listdir(directory):
            if filename.endswith(".m4a"):
                m4a_path = os.path.join(directory, filename)
                mp3_path = os.path.join(directory, filename[:-4] + ".mp3")
                try:
                    os.rename(m4a_path, mp3_path)
                    self.status_label.config(
                        text=f"Renamed {filename} to {filename[:-4] + '.mp3'}", fg="green"
                    )
                except OSError as e:
                    self.status_label.config(text=f"Error renaming {filename}: {e}", fg="red")

    def tag_audio(self, output_path):
        if output_path.endswith(".mp3"):
            try:
                self.add_id3_tags(output_path)
                add_bitrate_samplerate(input_file=output_path)
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

    def add_id3_tags(self, file_path):
        try:
            filename = os.path.basename(file_path)
            parts = filename.split(" - ")

            # --- Handle different filename patterns ---
            if len(parts) >= 2:  # Check if there's at least one " - " separator
                artist = parts[0].strip() # Assume artist is before the first " - "
                title = " - ".join(parts[1:]).replace(".mp3", "").strip()  # Join the rest for the title

                audio = EasyID3(file_path)
                audio["title"] = title
                audio["artist"] = artist
                audio.save()
            else:
                print(f"Could not extract artist and title from filename: {filename}")

        except Exception as e:
            print(f"Error adding ID3 tags: {e}")

    def yt_dlp_progress_hook(self, d):
        if d['status'] == 'downloading':
            downloaded_bytes = d['downloaded_bytes']
            total_bytes = d.get('total_bytes', 0)  # Use d.get() to safely get 'total_bytes'

            # Only calculate speed if total_bytes is available
            if total_bytes > 0:
                percentage_of_completion = (downloaded_bytes / total_bytes) * 100
                self.progress["value"] = percentage_of_completion

                elapsed_time = time.time() - self.start_time
                download_speed_bps = downloaded_bytes / elapsed_time if elapsed_time > 0 else 0

                if download_speed_bps >= 1024 * 1024:
                    download_speed = download_speed_bps / (1024 * 1024)
                    speed_unit = "MB/s"
                else:
                    download_speed = download_speed_bps / 1024
                    speed_unit = "KB/s"

                self.speed_label.config(text=f"Speed: {download_speed:.2f} {speed_unit}")

            self.update_idletasks() # Update GUI even if total_bytes is not available

    def tag_files_in_directory(self):
        directory = filedialog.askdirectory()
        if not directory:
            self.status_label.config(
                text=self.languages[self.current_language]["no_directory_selected"],
                fg="red",
            )
            return

        files_to_tag = [f for f in os.listdir(directory) if f.endswith(".mp3")]
        total_files = len(files_to_tag)

        if total_files == 0:
            self.status_label.config(
                text=self.languages[self.current_language]["no_mp3_files_found"],
                fg="red",
            )
            return

        self.current_video = 0
        for i, filename in enumerate(files_to_tag):
            file_path = os.path.join(directory, filename)
            try:
                self.add_id3_tags(file_path)
                add_bitrate_samplerate(input_file=file_path)
                self.status_label.config(
                    text=f"Audio tagged: {file_path}", fg="green"
                )
            except Exception as e:
                self.status_label.config(
                    text=f"Audio tagging failed: {e}", fg="red"
                )

            self.current_video = i + 1
            self.num_videos_label.config(
                text=f"Videos: {self.current_video}/{total_files}"
            )
            progress_percentage = (i + 1) / total_files * 100
            self.tagging_progressbar["value"] = progress_percentage
            self.update_idletasks()

        self.status_label.config(text="Tagging complete.", fg="green")


if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
