import os

# Get the base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERSION_FILE = os.path.join(BASE_DIR, 'VERSION')

try:
    # Read the version from the VERSION file
    with open(VERSION_FILE, 'r') as f:
        __version__ = f.read().strip()
except FileNotFoundError:
    # Fallback for development environments where the installer hasn't been run
    __version__ = "0.0.0-dev"
