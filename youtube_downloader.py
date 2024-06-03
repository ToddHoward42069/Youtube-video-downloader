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
        self.geometry("891x600")
        self.configure(bg="lightgray")

        self.url_label = tk.Label(self, text="YouTube URL:", bg="lightgray")
        self.url_label.pack(pady=10)
        
        self.url_entry = tk.Entry(self, width=50)
        self.url_entry.pack(pady=10)
        self.url_entry.bind("<KeyRelease>", self.delayed_fetch)

        self.status_label = tk.Label(self, text="", bg="lightgray")
        self.status_label.pack(pady=10)

        self.thumbnail_label = tk.Label(self, bg="lightgray")
        self.thumbnail_label.pack(pady=10)
        
        self.format_label = tk.Label(self, text="Select Format:", bg="lightgray")
        self.format_label.pack(pady=10)
        
        self.format_var = tk.StringVar(value="mp4")
        self.mp4_radio = tk.Radiobutton(self, text="MP4", variable=self.format_var, value="mp4", bg="lightgray")
        self.mp3_radio = tk.Radiobutton(self, text="MP3", variable=self.format_var, value="mp3", bg="lightgray")
        self.mp4_radio.pack()
        self.mp3_radio.pack()
        
        self.location_button = tk.Button(self, text="Select Download Location", command=self.select_location)
        self.location_button.pack(pady=10)
        
        self.download_button = tk.Button(self, text="Download", command=self.download_video)
        self.download_button.pack(pady=10)
        
        self.download_location = ""
        self.video = None
        self.fetch_job = None

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
            self.status_label.config(text="This video is unavailable", fg="red")
        except Exception as e:
            self.status_label.config(text=f"Failed to fetch video: {e}", fg="red")

    def select_location(self):
        self.download_location = filedialog.askdirectory()
        if self.download_location:
            self.status_label.config(text=f"Download location set to: {self.download_location}", fg="green")

    def download_video(self):
        if not self.video:
            self.status_label.config(text="No video fetched to download", fg="red")
            return

        if not self.download_location:
            self.status_label.config(text="Please select a download location", fg="red")
            return

        try:
            format_choice = self.format_var.get()
            if format_choice == "mp4":
                stream = self.video.streams.get_highest_resolution()
            elif format_choice == "mp3":
                stream = self.video.streams.filter(only_audio=True).first()
            
            output_path = stream.download(output_path=self.download_location)
            if format_choice == "mp3":
                base, ext = output_path.rsplit('.', 1)
                new_file = f"{base}.mp3"
                os.rename(output_path, new_file)
            
            self.status_label.config(text="Download completed", fg="green")
        except VideoUnavailable:
            self.status_label.config(text="This video is unavailable", fg="red")
        except Exception as e:
            self.status_label.config(text=f"Failed to download video: {e}", fg="red")

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
