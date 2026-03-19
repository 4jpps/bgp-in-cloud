import subprocess
import datetime
import os
import sys

# --- Configuration ---
# The absolute path to your local Git repository.
REPO_PATH = os.path.dirname(os.path.abspath(__file__))
# The name of the branch you want to push to.
BRANCH_NAME = "master"
# The path to the log file.
LOG_FILE = os.path.join(REPO_PATH, "git_sync.log")

def log(message):
    """Appends a formatted message to the log file."""
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")

def run_command(command):
    """Runs a shell command, logs its output, and handles errors."""
    try:
        # Execute the command from the repository's directory.
        result = subprocess.run(
            command, 
            cwd=REPO_PATH, 
            check=True, 
            capture_output=True, 
            text=True, 
            shell=True
        )
        log(f"SUCCESS: Ran '{command}'.\nOutput:\n{result.stdout}")
        return result
    except subprocess.CalledProcessError as e:
        error_message = (
            f"ERROR: Command '{command}' failed with return code {e.returncode}.\n"
            f"Stderr:\n{e.stderr}\n"
            f"Stdout:\n{e.stdout}"
        )
        log(error_message)
        # Exit the script with an error code if any command fails.
        sys.exit(1)

def main():
    """Main function to perform the Git sync operation."""
    log("--- Starting automated Git sync ---")

    # 1. Idempotency Check: See if there are any changes to commit.
    status_result = subprocess.run("git status --porcelain", cwd=REPO_PATH, capture_output=True, text=True, shell=True)
    if not status_result.stdout.strip():
        log("No changes detected. Exiting gracefully.")
        print("No changes to commit.")
        return

    # 2. Stage all new and modified files.
    run_command("git add .")

    # 3. Generate a dynamic commit message.
    commit_message = f"Automated commit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 4. Commit the changes.
    run_command(f'git commit -m "{commit_message}"')

    # 5. Push the changes to the remote repository.
    run_command(f"git push origin {BRANCH_NAME}")

    log("--- Git sync completed successfully ---")
    print("Changes have been successfully committed and pushed.")

if __name__ == "__main__":
    main()
