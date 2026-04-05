import sys
import os
from .loader import NB_finder
import threading
import subprocess


# Cache and PID paths
PROJECT_ROOT = os.getcwd()
SHADOW_DIR = os.path.join(PROJECT_ROOT, ".easyJupyter_cache")
PID_FILE = os.path.join(SHADOW_DIR, "watcher.pid")


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
    except (OSError, ValueError):
        # Process is dead or file is corrupted
        return False


def register_hook():
    """
    This function is called by the .pth file when Python interpreter starts up.
    It registers the import hook to the sys.meta_path and starts the watcher.
    """
    if not any(isinstance(x, NB_finder) for x in sys.meta_path):
        sys.meta_path.insert(0, NB_finder())

        # Create cache directory if it doesn't exist
        os.makedirs(SHADOW_DIR, exist_ok=True)

        # Spawn daemon only if it isn't already running
        if not is_watcher_running():
            subprocess.Popen(
                [sys.executable, "-m", "EasyJupyter.watcher"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

# Automatically execute when the user imports the library
register_hook()