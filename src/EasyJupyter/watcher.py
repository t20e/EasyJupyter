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
from . import is_watcher_running
import datetime

# Cache and PID paths
PROJECT_ROOT = os.getcwd()
SHADOW_DIR = os.path.join(PROJECT_ROOT, ".easyJupyter_cache")
PID_FILE = os.path.join(SHADOW_DIR, "watcher.pid")


class AutoSyncHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if ".easyJupyter_cache" in event.src_path:
            return
        if event.is_directory or not event.src_path.endswith(".ipynb"):
            return

        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] DEBUG: Change detected in {event.src_path}")

            # Give the OS a moment to release the file lock
            time.sleep(0.05)
            loader = EasyJupyterLoader(event.src_path)
            loader.get_code()
            print(f"[{timestamp}] DEBUG: Successfully synced {event.src_path}")
            sys.stdout.flush() # Force write to the log file

        except Exception as e:
            import traceback
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] CRITICAL ERROR: Failed to sync {event.src_path}")
            traceback.print_exc()
            sys.stdout.flush() 

def cleanup_pid():
    """Remove the PID file when the watcher shuts down."""
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


def start_daemon():
    if is_watcher_running():
        return
    
    os.makedirs(SHADOW_DIR, exist_ok=True)
    
    # Write the current process PID to the lock file
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    # Register cleanup
    atexit.register(cleanup_pid)

    # Start watchdog
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] DEBUG: Watchdog daemon starting.")
    observer = Observer()
    observer.schedule(AutoSyncHandler(), path=".", recursive=True)
    observer.start()

    try:
        while True:
            # Check if the background thread died
            if not observer.is_alive(): # Check if the background thread died
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] Fatal error: Watchdog thread died. Exiting daemon...")
                exit(1)

            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    start_daemon()
