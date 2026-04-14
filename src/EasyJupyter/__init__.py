import sys
import os
import subprocess
from rich.console import Console
from rich.theme import Theme
from .utils import get_project_root

# Define global variables
VSC_SETTINGS_UPDATED = False
UPDATED_NOTEBOOKS = []  # Keep track of what notebooks the user has updated
PROJECT_ROOT = get_project_root()
SHADOW_DIR = os.path.join(PROJECT_ROOT, ".easyJupyter_cache")

# Cache and PID paths
PID_FILE = os.path.join(SHADOW_DIR, "watcher.pid")

# Rich library theme
custom_theme = Theme(
    {
        "label": "bold default",
        "path": "cyan",
        "cell_location": "yellow",
    }
)
console = Console(theme=custom_theme)

# Import NB_finder after above variables are defined to avoid circular imports!
from .loader import NB_finder

def is_watcher_running():
    """Check if a watcher is running by checking PID lock file."""
    if not os.path.exists(PID_FILE):
        return False

    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())

        # os.kill with signal 0 does not kill the process;
        # it just checks if the OS will allow a signal to be sent (i.e., process exists).
        os.kill(pid, 0)
        return True
    except (OSError, ValueError, FileNotFoundError):
        # If the process isn't running or the file is corrupted, it's safe to restart
        return False


def register_hook():
    """
    This function is called by the .pth file when Python interpreter starts up. It registers the import hook to the sys.meta_path and starts the watcher.
    """
    if not any(isinstance(x, NB_finder) for x in sys.meta_path):
        sys.meta_path.insert(0, NB_finder())

        # Add project root to sys.path to enable cross-folder notebook imports
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)

        # Create cache directory if it doesn't exist
        os.makedirs(SHADOW_DIR, exist_ok=True)

        # Spawn daemon only if it isn't already running, and we aren't running a CLI command or the watcher manually with `python -m EasyJupyter.watcher`
        is_watcher_script = any("watcher" in arg for arg in sys.argv)
        is_cli_script = os.path.basename(sys.argv[0]) in ["easyjupyter", "easyjupyter.exe", "cli.py"] or "EasyJupyter.cli" in sys.argv
        if not is_watcher_running() and not is_watcher_script and not is_cli_script:
            # print("[EasyJupyter] Spawning background watcher...")

            # Open a log file to catch any background daemon errors
            log_path = os.path.join(SHADOW_DIR, "watcher.log")
            log_file = open(log_path, "a")

            subprocess.Popen(
                [sys.executable, "-u", "-m", "EasyJupyter.watcher"],
                stdin=subprocess.DEVNULL,
                stdout=log_file,  # Route logs to the hidden cache folder
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        # else:
        #     print("[EasyJupyter] Watcher is already running.")


# Automatically execute when the user imports the library
register_hook()
