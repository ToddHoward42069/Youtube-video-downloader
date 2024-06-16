import subprocess
import os
import tempfile
import shutil  # Import shutil for copying files

def add_bitrate_samplerate(input_file, bitrate="320k", samplerate="44100"):
    """Adds bitrate and samplerate to the input file, overwriting the original."""
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file.close()  # Close the file so FFmpeg can access it

        # Run FFmpeg command, writing to the temporary file
        subprocess.run([
            "ffmpeg",
            "-i", input_file,
            "-b:a", bitrate,
            "-ar", samplerate,
            "-y",  # Force overwrite (placed before output file)
            temp_file.name 
        ], check=True)

        # Copy the temporary file to the original file's location
        shutil.copyfile(temp_file.name, input_file)

        # Delete the temporary file
        os.remove(temp_file.name)

        print(f"FFmpeg script executed successfully. File modified: {input_file}")

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg script failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")