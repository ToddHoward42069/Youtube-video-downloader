# Use the official Python image from the Docker Hub
FROM python:3.9.5

# Set the working directory in the container
WORKDIR /youtube_downloader

# Copy the current directory contents into the container at /youtube_downloader
COPY . /youtube_downloader/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run the youtube_downloader.py when the container launches
CMD ["python", "main.py"]