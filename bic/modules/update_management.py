import httpx
from packaging.version import parse as parse_version
from bic.__version__ import __version__ as local_version

REPO_URL = "https://api.github.com/repos/4jpps/bgp-in-cloud/releases/latest"

def get_latest_version():
    """Fetches the latest version tag from the GitHub repository."""
    try:
        with httpx.Client() as client:
            response = client.get(REPO_URL)
            response.raise_for_status()
            data = response.json()
            return data['tag_name'].lstrip('v') # Remove leading 'v' if present
    except (httpx.HTTPStatusError, httpx.RequestError):
        return None

def is_update_available():
    """Compares the local version to the latest remote version."""
    latest_ver = get_latest_version()
    if not latest_ver:
        return None, None # Cannot determine remote version
    
    if parse_version(latest_ver) > parse_version(local_version):
        return latest_ver, get_release_notes(latest_ver)
    return None, None

def get_release_notes(version_tag):
    """Fetches the release notes for a specific version tag."""
    release_url = f"https://api.github.com/repos/4jpps/bgp-in-cloud/releases/tags/v{version_tag}"
    try:
        with httpx.Client() as client:
            response = client.get(release_url)
            response.raise_for_status()
            data = response.json()
            return data.get('body', 'No release notes found.')
    except (httpx.HTTPStatusError, httpx.RequestError):
        return "Could not retrieve changelog."
