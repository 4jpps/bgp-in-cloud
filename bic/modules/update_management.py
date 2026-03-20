import httpx
import os
import shutil
import zipfile
import subprocess
from pathlib import Path
from packaging.version import parse as parse_version
from bic.__version__ import __version__ as local_version

REPO_URL = "https://api.github.com/repos/4jpps/bgp-in-cloud/releases/latest"

def get_latest_version(db_core):
    # ... (code remains the same) ...
    return None

def is_update_available(db_core):
    # ... (code remains the same) ...
    return None, None

def get_release_notes(version_tag):
    # ... (code remains the same) ...
    return "Could not retrieve changelog."

def perform_update():
    """Downloads and applies the latest update."""
    try:
        with httpx.Client() as client:
            response = client.get(REPO_URL)
            response.raise_for_status()
            data = response.json()
            zip_url = data['zipball_url']

            # Download the zip file
            zip_response = client.get(zip_url, follow_redirects=True)
            zip_response.raise_for_status()
            
            zip_path = Path("/tmp/update.zip")
            zip_path.write_bytes(zip_response.content)

            # Extract and update
            extract_path = Path("/tmp/update_ext")
            if extract_path.exists(): shutil.rmtree(extract_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # The extracted folder has a dynamic name, find it
            extracted_folder = next(extract_path.iterdir())
            
            # Simple copy and overwrite
            core_files_updated = False
            for item in extracted_folder.iterdir():
                dest = Path.cwd() / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
                if item.name in ["webapp.py", "core.py"]:
                    core_files_updated = True
            
            if core_files_updated:
                # This is a simple way to trigger a restart with Uvicorn's reloader
                # A more robust solution might use a process manager
                (Path.cwd() / "touch_to_reload").touch()

            return {"success": True, "message": "Update applied. Restart if needed."}

    except Exception as e:
        return {"success": False, "message": str(e)}
