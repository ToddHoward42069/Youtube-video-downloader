import tkinter as tk
from tkinter import filedialog
from pytube import YouTube
from pytube.exceptions import VideoUnavailable
from PIL import Image, ImageTk
import io
import requests
import os
import ssl
import certifi

# Ensure that the certifi certificates are used
os.environ['SSL_CERT_FILE'] = certifi.where()

class YouTubeDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Video Downloader")
        self.geometry("600x650")
        self.configure(bg="#2b2b2b")

        # Title Label
        self.title_label = tk.Label(self, text="YouTube Video Downloader", font=("Helvetica", 18, "bold"), bg="#2b2b2b", fg="white")
        self.title_label.pack(pady=20)

        # URL Frame
        self.url_frame = tk.Frame(self, bg="#2b2b2b")
        self.url_frame.pack(pady=10)

        self.url_label = tk.Label(self.url_frame, text="YouTube URL:", font=("Helvetica", 12), bg="#2b2b2b", fg="white")
        self.url_label.pack(side=tk.LEFT, padx=10)

        self.url_entry = tk.Entry(self.url_frame, width=40, font=("Helvetica", 12))
        self.url_entry.pack(side=tk.LEFT, padx=10)
        self.url_entry.bind("<KeyRelease>", self.delayed_fetch)
        self.url_entry.bind("<Control-a>", self.select_all)
        self.url_entry.bind("<Control-A>", self.select_all)  # For uppercase 'A'

        # Status Label
        self.status_label = tk.Label(self, text="", font=("Helvetica", 10), bg="#2b2b2b", fg="red")
        self.status_label.pack(pady=10)

        # Thumbnail Label
        self.thumbnail_label = tk.Label(self, bg="#2b2b2b")
        self.thumbnail_label.pack(pady=10)

        # Format Frame
        self.format_frame = tk.Frame(self, bg="#2b2b2b")
        self.format_frame.pack(pady=10)

        self.format_label = tk.Label(self.format_frame, text="Select Format:", font=("Helvetica", 12), bg="#2b2b2b", fg="white")
        self.format_label.pack(side=tk.LEFT, padx=10)

        self.format_var = tk.StringVar(value="mp4")
        self.mp4_radio = tk.Radiobutton(self.format_frame, text="MP4", variable=self.format_var, value="mp4", font=("Helvetica", 12), bg="#2b2b2b", fg="white", selectcolor="#2b2b2b")
        self.mp3_radio = tk.Radiobutton(self.format_frame, text="MP3", variable=self.format_var, value="mp3", font=("Helvetica", 12), bg="#2b2b2b", fg="white", selectcolor="#2b2b2b")
        self.mp4_radio.pack(side=tk.LEFT, padx=10)
        self.mp3_radio.pack(side=tk.LEFT, padx=10)

        # Location Button
        self.location_button = tk.Button(self, text="Select Download Location", font=("Helvetica", 12), bg="#4CAF50", fg="white", command=self.select_location)
        self.location_button.pack(pady=10)

        # Download Button
        self.download_button = tk.Button(self, text="Download", font=("Helvetica", 12), bg="#008CBA", fg="white", command=self.download_video)
        self.download_button.pack(pady=10)

        # Download from File Button
        self.file_download_button = tk.Button(self, text="Download from File", font=("Helvetica", 12), bg="#f44336", fg="white", command=self.download_from_file)
        self.file_download_button.pack(pady=10)

        self.download_location = ""
        self.video = None
        self.fetch_job = None

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
            self.status_label.config(text="Please enter a YouTube URL", fg="red")
            return

        try:
            self.video = YouTube(url)
            response = requests.get(self.video.thumbnail_url)
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            image = image.resize((320, 180), Image.Resampling.LANCZOS)
            thumbnail = ImageTk.PhotoImage(image)
            self.thumbnail_label.config(image=thumbnail)
            self.thumbnail_label.image = thumbnail
            self.status_label.config(text="Video fetched successfully", fg="green")
        except VideoUnavailable:
            self.thumbnail_label.config(image='')
            self.status_label.config(text="This video is unavailable", fg="red")
        except Exception as e:
            self.thumbnail_label.config(image='')
            self.status_label.config(text=f"Failed to fetch video: {e}", fg="red")

    def select_location(self):
        self.download_location = filedialog.askdirectory()
        if self.download_location:
            self.status_label.config(text=f"Download location set to: {self.download_location}", fg="green")

    def get_download_location(self):
        return self.download_location if self.download_location else os.getcwd()

    def download_video(self):
        if not self.video:
            self.status_label.config(text="No video fetched to download", fg="red")
            return

        download_location = self.get_download_location()

        try:
            format_choice = self.format_var.get()
            if format_choice == "mp4":
                stream = self.video.streams.get_highest_resolution()
            elif format_choice == "mp3":
                stream = self.video.streams.filter(only_audio=True).first()

            output_path = stream.download(output_path=download_location)
            if format_choice == "mp3":
                base, ext = output_path.rsplit('.', 1)
                new_file = f"{base}.mp3"
                os.rename(output_path, new_file)

            self.status_label.config(text="Download completed", fg="green")
        except VideoUnavailable:
            self.status_label.config(text="This video is unavailable", fg="red")
        except Exception as e:
            self.status_label.config(text=f"Failed to download video: {e}", fg="red")

    def download_from_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not file_path:
            self.status_label.config(text="No file selected", fg="red")
            return

        download_location = self.get_download_location()

        try:
            with open(file_path, 'r') as file:
                urls = file.readlines()
            for url in urls:
                url = url.strip()
                if url:
                    try:
                        video = YouTube(url)
                        format_choice = self.format_var.get()
                        if format_choice == "mp4":
                            stream = video.streams.get_highest_resolution()
                        elif format_choice == "mp3":
                            stream = video.streams.filter(only_audio=True).first()

                        output_path = stream.download(output_path=download_location)
                        if format_choice == "mp3":
                            base, ext = output_path.rsplit('.', 1)
                            new_file = f"{base}.mp3"
                            os.rename(output_path, new_file)
                    except VideoUnavailable:
                        self.status_label.config(text=f"Video unavailable: {url}", fg="red")
                    except Exception as e:
                        self.status_label.config(text=f"Failed to download video: {e}", fg="red")

            self.status_label.config(text="All downloads completed", fg="green")
        except Exception as e:
            self.status_label.config(text=f"Error reading file: {e}", fg="red")

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
