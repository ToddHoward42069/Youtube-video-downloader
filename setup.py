# setup.py
from distutils.core import setup
import py2exe

setup(
    console=['youtube_downloader.py'],
    options={
        'py2exe': {
            'bundle_files': 1,  # Bundle everything into a single file
            'compressed': True,
        }
    },
    zipfile=None,
)
