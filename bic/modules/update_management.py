#!/usr/bin/env python
"""
This module provides functionality for checking for and applying application updates
from a GitHub repository.
"""

import httpx
import os
import shutil
import zipfile
import tempfile
from pathlib import Path
from packaging.version import parse as parse_version
from bic.__version__ import __version__ as local_version
from bic.core import get_logger

# Initialize logger
log = get_logger(__name__)

# The GitHub API URL for the latest release
REPO_URL = "https://api.github.com/repos/4jpps/bgp-in-cloud/releases/latest"

def get_latest_version() -> str | None:
    """Fetches the latest release version tag from the project's GitHub repository.

    This function queries the GitHub API for the latest release and extracts the
    tag name, which is assumed to be the version number.

    Returns:
        The latest version tag as a string (e.g., "v1.2.3"), or None if the
        request fails or the tag cannot be found.
    """
    log.info(f"Checking for latest version at {REPO_URL}")
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(REPO_URL, follow_redirects=True)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            data = response.json()
            latest_tag = data.get('tag_name')
            log.info(f"Found latest version tag: {latest_tag}")
            return latest_tag
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            log.warning("No public releases found on GitHub repository. Cannot check for updates.")
            return None # Return None if no releases are found
        else:
            log.error(f"An HTTP error occurred while fetching latest version: {e}")
    except httpx.RequestError as e:
        log.error(f"An error occurred while requesting {e.request.url!r}: {e}")
    except Exception as e:
        log.error(f"An unexpected error occurred while fetching latest version: {e}", exc_info=True)
    return None

def is_update_available() -> tuple[bool, str | None]:
    """Compares the local version with the latest version from GitHub.

    It uses the `packaging.version.parse` method for a robust, PEP 440-compliant
    version comparison.

    Returns:
        A tuple containing:
        - bool: True if an update is available, False otherwise.
        - str | None: The latest version string, or None if it couldn't be fetched.
    """
    latest_version_str = get_latest_version()
    if not latest_version_str:
        return False, None

    try:
        local = parse_version(local_version)
        latest = parse_version(latest_version_str)
        log.info(f"Comparing local version {local} with latest version {latest}")
        return latest > local, latest_version_str
    except TypeError as e:
        log.error(f"Could not parse version strings for comparison: {e}")
        return False, latest_version_str

def get_release_notes(version_tag: str) -> str:
    """Retrieves the release notes (body) for a specific version tag from GitHub.

    Args:
        version_tag: The version tag to fetch release notes for (e.g., "v1.2.3").

    Returns:
        A string containing the release notes in Markdown format, or an error message.
    """
    release_url = f"https://api.github.com/repos/4jpps/bgp-in-cloud/releases/tags/{version_tag}"
    log.info(f"Fetching release notes from {release_url}")
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(release_url)
            response.raise_for_status()
            data = response.json()
            return data.get('body', "No release notes found for this version.")
    except httpx.RequestError as e:
        log.error(f"Failed to fetch release notes: {e}")
        return "Error: Could not retrieve release notes from GitHub."

def perform_update() -> dict:
    """Downloads and applies the latest update from GitHub.

    This function performs the following steps:
    1. Fetches the latest release information from the GitHub API.
    2. Downloads the release zipball to a temporary directory.
    3. Extracts the zip file.
    4. Performs a targeted update by copying the new 'bic' source directory
       over the existing one.
    5. Touches a file (`touch_to_reload`) to trigger a reload if an auto-reloader
       like uvicorn is being used in development.

    Returns:
        A dictionary with a "success" status and a message for the user.
    """
    log.info("--- Starting application update process ---")
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(REPO_URL)
            response.raise_for_status()
            data = response.json()
            zip_url = data.get('zipball_url')
            if not zip_url:
                return {"success": False, "message": "Could not find download URL in GitHub API response."}

            log.info(f"Downloading update from {zip_url}")
            zip_response = client.get(zip_url, follow_redirects=True)
            zip_response.raise_for_status()

            # Use a temporary directory for all update operations
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                zip_path = tmp_path / "update.zip"
                extract_path = tmp_path / "update_ext"

                log.debug(f"Saving downloaded zip to {zip_path}")
                zip_path.write_bytes(zip_response.content)

                log.debug(f"Extracting zip file to {extract_path}")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)

                # The extracted folder has a dynamic name, find it
                extracted_folder = next(extract_path.iterdir())
                log.info(f"Update extracted to: {extracted_folder}")

                # --- Safer, Targeted Update Logic ---
                # Instead of overwriting the whole directory, only update the 'bic' source folder.
                source_bic_dir = extracted_folder / 'bic'
                dest_bic_dir = Path.cwd() / 'bic'

                if not source_bic_dir.is_dir():
                    return {"success": False, "message": "Update archive is malformed; 'bic' directory not found."}

                log.info(f"Updating application source from {source_bic_dir} to {dest_bic_dir}")
                shutil.copytree(source_bic_dir, dest_bic_dir, dirs_exist_ok=True)

                # Trigger a reload if uvicorn is watching. This remains a simple mechanism.
                log.warning("Update applied. Triggering application reload by touching file.")
                (Path.cwd() / "touch_to_reload").touch()

                return {"success": True, "message": "Update applied successfully. Application is restarting."}

    except httpx.RequestError as e:
        log.error(f"Update failed during download: {e}")
        return {"success": False, "message": f"Download failed: {e}"}
    except (zipfile.BadZipFile, FileNotFoundError) as e:
        log.error(f"Update failed during extraction: {e}")
        return {"success": False, "message": f"Extraction failed: {e}"}
    except Exception as e:
        log.critical(f"An unexpected critical error occurred during the update process: {e}", exc_info=True)
        return {"success": False, "message": f"A critical error occurred: {e}"}
