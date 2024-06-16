# ffmpeg_script.py

import subprocess
import os
import tempfile
import shutil

def add_bitrate_samplerate(input_file, bitrate="320k", samplerate="44100"):
    """Adds bitrate and samplerate to the input file, overwriting the original."""
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file.close() 

        # Construct the FFmpeg command
        command = [
            "ffmpeg",
            "-i", input_file,
            "-b:a", bitrate,
            "-ar", samplerate,
            "-y", 
            temp_file.name
        ]

        # Run FFmpeg command
        subprocess.run(command, check=True)

        # Copy the temporary file to the original file's location
        shutil.copyfile(temp_file.name, input_file)

        # Delete the temporary file
        os.remove(temp_file.name)

        print(f"FFmpeg script executed successfully. File modified: {input_file}")

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg script failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")