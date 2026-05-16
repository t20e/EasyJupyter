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
from . import PROJECT_ROOT, SHADOW_DIR, is_watcher_running
import datetime
from pathlib import Path

# Cache and PID paths
PID_FILE = Path(SHADOW_DIR) / "watcher.pid"


class AutoSyncHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_modified = {}
        self.debounce_secs = 0.25 # Debounce mechanism to throttle the execution rate.
        # NOTE: It executes on the first save and locks subsequent events for 0.25 seconds (milliseconds).
        #       While this handles manual human saves well, automated tools (like code formatters) may 
        #       trigger a second save within this 0.25s lockout window
        #       Because the second save falls inside the lockout, it is ignored, leaving the cache out 
        #       of sync with the final file state.

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".ipynb"):
            return
    
        # Ignore cache and hidden jupyter checkpoint files
        if ".easyJupyter_cache" in event.src_path or ".ipynb_checkpoints" in event.src_path:
            return

        # Debounce logic to prevent thrashing on multi-event saves
        current_time = time.time()
        if event.src_path in self.last_modified:
            if current_time -self.last_modified[event.src_path] < self.debounce_secs:
                return
        self.last_modified[event.src_path] = current_time

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
    if PID_FILE.exists():
        os.remove(PID_FILE)


def start_daemon():
    if is_watcher_running():
        print(f"Watcher daemon is already running! (See PID file: {PID_FILE})")
        print("If you want to restart it manually, please stop the current background process or delete the PID file.")
        return
    
    SHADOW_DIR.mkdir(exist_ok=True)
    
    # Write the current process PID to the lock file
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    # Register cleanup
    atexit.register(cleanup_pid)

    # Start watchdog
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] DEBUG: Watchdog daemon starting.")
    observer = Observer()
    observer.schedule(AutoSyncHandler(), path=str(PROJECT_ROOT), recursive=True)
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
