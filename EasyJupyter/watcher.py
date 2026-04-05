"""
Handles the Watchdog observer. It watches for changes in the notebook files and updates the cache.
"""

import os
import time
import sys
import atexit
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .loader import EasyJupyterLoader

# Cache and PID paths
PROJECT_ROOT = os.getcwd()
SHADOW_DIR = os.path.join(PROJECT_ROOT, ".easyJupyter_cache")
PID_FILE = os.path.join(SHADOW_DIR, "watcher.pid")


class AutoSyncHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".ipynb") and SHADOW_DIR not in event.src_path:
            loader = EasyJupyterLoader(event.src_path)
            loader.get_code()

def cleanup_pid():
    """Remove the PID file when the watcher shuts down."""
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

def start_daemon():
    
    # Write the current process PID to the lock file
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    # Register cleanup
    atexit.register(cleanup_pid)

    # Start watchdog
    observer = Observer()
    observer.schedule(AutoSyncHandler(), path=".", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_daemon()