import types
import nbformat
import sys
from types import ModuleType
import os
import sys
import linecache
import importlib.abc
import importlib.util
import traceback
import atexit
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from rich.table import Table
import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
import argparse
from rich.progress import track

VSC_SETTINGS_UPDATED = False
UPDATED_NOTEBOOKS = []  # Track what notebooks the user has updated

# TODO when i add "python.analysis.extraPaths": ["./typings"] for VSC intellisense, make sure to tell user to do that both in the repo, and when they first run the code, to check if first time running, check if the cache folder exists~

# Rich library theme
custom_theme = Theme(
    {
        "label": "bold default",
        "path": "cyan",
        "cell_location": "yellow",
    }
)
console = Console(theme=custom_theme)


# TODO this clean up deletes the whole cache dir instead of just a couple files!
def cleanup_cache():
    """
    If user renames or deletes a notebook, also delete its cache file

    Run with: `python EasyJupyter.py --clean`
    """
    if os.path.exists(EasyJupyterLoader.SHADOW_DIR):
        shutil.rmtree(EasyJupyterLoader.SHADOW_DIR)
        console.print(
            f"[bold red]🗑️  Cache cleared:[/bold red] {EasyJupyterLoader.SHADOW_DIR}"
        )
    else:
        console.print("[yellow]No cache found to clear.[/yellow]")


def add_to_vsc_settings(SHADOW_DIR: str):
    """
    Add `"python.analysis.extraPaths": ["./.easyJupyter_cache"]` to ".vscode/settings.json" so VSC's Pylance intellisense works with imported notebooks.

    Arg:
        SHADOW_DIR: ".easyJupyter_cache"

    """
    vscode_dir = os.path.join(os.getcwd(), ".vscode")
    settings_path = os.path.join(vscode_dir, "settings.json")
    vsc_path = f"./{SHADOW_DIR}"

    if not os.path.exists(vscode_dir):
        os.makedirs(vscode_dir)

    # TODO wont this run for every notebook, it should only run once, if .easyJupyter_cache hasn't been created yet, or just check if the setting is in settings.json
    settings = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r") as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            settings = {}

    extra_paths = settings.get("python.analysis.extraPaths", [])

    if vsc_path not in extra_paths:
        extra_paths.append(vsc_path)
        settings["python.analysis.extraPaths"] = extra_paths

        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=4)

        print(
            "Added `'python.analysis.extraPaths': ['.easyJupyter_cache']` setting to .vscode/settings.json"
        )


def sync_all():
    """
    When user updates a Notebook sync it to its cache file
    """
    global UPDATED_NOTEBOOKS
    root_dir = "."

    # clear list
    UPDATED_NOTEBOOKS = []

    all_nb = []
    for root, _, files in os.walk(root_dir):
        if EasyJupyterLoader.SHADOW_DIR in root:
            continue  # skip the cache dir
        all_nb.extend([os.path.join(root, f) for f in files if f.endswith(".ipynb")])

    if all_nb:
        for nb_path in track(all_nb, description="[cyan]Syncing Notebooks..."):
            # Create a loader instance for each notebook to trigger the sync
            loader = EasyJupyterLoader(nb_path)
            loader.get_code()
        console.print("[bold green]Sync Complete![/bold green]")
    else:
        console.print("[yellow]No notebooks updated![/yellow]")


def print_nb_update_report():
    if not UPDATED_NOTEBOOKS:
        return

    # TODO compress filenames for nested files, they are to long example: .easyJupyter_cache/shadow_tes
    table = Table(
        title="Notebook Updates",
        title_style="label",
        show_header=True,
        header_style="bold default",
    )
    table.add_column("Notebook File Updated", style="path", width=45)
    table.add_column("Cache Updated At", style="cell_location", width=45)

    for nb_rel_path, shadow_path in UPDATED_NOTEBOOKS:

        display_nb = (nb_rel_path[:42] + "..") if len(nb_rel_path) > 44 else nb_rel_path

        table.add_row(nb_rel_path, shadow_path)

    console.print(table)


atexit.register(print_nb_update_report)


class NB_finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        # Look for the notebook ile in the expected path
        mod_name = fullname.split(".")[-1]
        search_paths = path or [os.getcwd()]

        # Search for the notebook
        for p in search_paths:
            nb_path = os.path.join(p, f"{mod_name}.ipynb")
            if os.path.exists(nb_path):
                return importlib.util.spec_from_file_location(
                    fullname, nb_path, loader=EasyJupyterLoader(nb_path)
                )

        return None  # Notebook not found


class EasyJupyterLoader(importlib.abc.Loader):

    IGNORE_CELL_SYNTAX = "# @i-c"
    IGNORE_LINE = "# @i-l"
    PROJECT_ROOT = os.path.abspath(os.curdir)
    SHADOW_DIR = ".easyJupyter_cache"

    def __init__(self, path):
        self.path = path

    def create_module(self, spec):
        """Import the notebook as a module"""

        global VSC_SETTINGS_UPDATED

        # Append shadow path to sys.path for jupyter lab, #TODO test if this is needed
        if self.SHADOW_DIR not in sys.path:
            sys.path.append(os.path.abspath(self.SHADOW_DIR))

        if not VSC_SETTINGS_UPDATED:
            add_to_vsc_settings(self.SHADOW_DIR)
            VSC_SETTINGS_UPDATED = True

        return types.ModuleType(spec.name)

    def exec_module(self, module):

        # Check if we already transformed the notebook, and it has not been updated since.
        code = self.get_code()

        # Handle relative imports and metadata
        module.__file__ = self.path
        # Use spec.parent to set the package for relative imports
        if hasattr(module, "__spec__"):
            module.__package__ = module.__spec__.parent

        # Execute with error interception
        try:
            exec(code, module.__dict__)
        except Exception as e:
            self.report_notebook_error(e)

    def get_code(self):
        """Returns code from cache if it has not been updated since"""
        py_cache_filename = os.path.basename(self.path).replace(".ipynb", ".py")
        shadow_path = os.path.join(self.SHADOW_DIR, py_cache_filename)

        if not os.path.exists(self.SHADOW_DIR):  # Ensure cache dir exists
            os.makedirs(self.SHADOW_DIR)

        # Check timestamps
        if os.path.exists(shadow_path):
            nb_mtime = os.path.getmtime(self.path)
            shadow_mtime = os.path.getmtime(shadow_path)

            if shadow_mtime > nb_mtime:
                # Cache is fresh, read and return it
                with open(shadow_path, "r") as f:
                    return f.read()

        # Else notebook was updated, re-transform it and save to cache
        return self.transform_notebook()

    def write_shadow_ref(self, code):
        """Create a shadow_{notebook_filename} to store the transformed contents of a notebook"""

        # Ensure hidden cache dir exists
        if not os.path.exists(self.SHADOW_DIR):
            os.makedirs(self.SHADOW_DIR)

        py_cache_filename = os.path.basename(self.path).replace(".ipynb", ".py")
        shadow_path = os.path.join(self.SHADOW_DIR, py_cache_filename)

        # Write the shadow file
        with open(shadow_path, "w") as f:
            f.write(code)

        # Print to show what notebooks were updated
        nb_rel_path = os.path.relpath(self.path, self.PROJECT_ROOT)

        # TODO call update here
        UPDATED_NOTEBOOKS.append((nb_rel_path, shadow_path))

    def transform_notebook(self):
        """
        Parse a notebook: Comes as JSON and apply ignore syntax.
        """

        with open(self.path, "r") as f:
            notebook = nbformat.read(f, as_version=4)

        nb_cells = notebook["cells"]
        nb_metadata = notebook["metadata"]
        nb_format = notebook["nbformat"]
        nb_nbformat_minor = notebook["nbformat_minor"]

        # Warnings to tell user if they used a skip line syntax but it has an empty line below it, or other warnings
        # TODO add all warnings checks possible
        warnings = []

        # Extract code to execute from the notebook
        exec_code_extract = []

        for cell_idx, cell in enumerate(nb_cells):
            lines = cell.source.splitlines()

            # Start each cell with a header comment for dev, makes the "shadow file" readable and help VSC search
            exec_code_extract.append(f"# {'='*64}")
            exec_code_extract.append(f"# CELL {cell_idx} | ID: {cell.id}")
            exec_code_extract.append(f"# {'='*64}")

            if cell.cell_type != "code" or any(
                l.strip().startswith(self.IGNORE_CELL_SYNTAX) for l in lines
            ):
                for line in lines:
                    exec_code_extract.append(f"# [Ignored Cell] {line}")
            else:
                # Process lines
                skip_next = False
                for line in lines:
                    clean = line.strip()

                    # If this line is a trigger, comment it out and prepare to skip the next line
                    if clean.startswith(self.IGNORE_LINE):
                        exec_code_extract.append(f"# {line}")
                        skip_next = True
                        continue  # Move to next line

                    # If skip_next si active, comment this line out and reset skip, this is to catch redundant skip lines stacked on top of each other
                    elif skip_next:  # TODO ADD WARNING
                        exec_code_extract.append(f"# [skip line] {line}")
                        skip_next = False
                    else:  # Regular code to execute line
                        exec_code_extract.append(line)

            exec_code_extract.append("")  # Add a next line

        final_code = "\n".join(exec_code_extract)

        self.write_shadow_ref(final_code)

        # Return final code to exec
        return final_code

    def report_notebook_error(self, error):
        # Extract the traceback info
        etype, evalue, tb = sys.exc_info()

        stack = traceback.extract_tb(tb)  # returns a list of FrameSummary objects

        # Get the last frame (where the actual error occurred)
        last_frame = stack[-1]
        line_no = last_frame.lineno

        # Locate the shadow file to find the context to share to user
        py_cache_filename = os.path.basename(self.path).replace(".ipynb", ".py")
        shadow_path = os.path.join(self.SHADOW_DIR, py_cache_filename)

        # Find which Cell caused the error
        target_cell = "Unknown"
        all_lines = []

        if os.path.exists(shadow_path):
            with open(shadow_path, "r") as f:
                all_lines = f.readlines()
                # Loop backward from the error line to find the last '# CELL' header
                for i in range(line_no - 1, -1, -1):
                    if all_lines[i].startswith("# CELL"):
                        target_cell = all_lines[i].strip("# ").strip()
                        break

        # print the note-book first error report
        error_message = (
            f"[label]Notebook:[/label] [path]{os.path.basename(self.path)}[/path]\n"
            f"[label]Location:[/label] [cell_location]{target_cell}[/cell_location]\n"
            f"[label]Code:[/label] {all_lines[line_no-1].strip()}"
        )

        console.print(
            Panel(
                error_message,
                title=f"[bold red]EasyJupyter Error: {type(error).__name__}[/bold red]",
                border_style="red",
            )
        )

        # TODO: Add a verbose flag, for example if the error occured in Pytorch, my error above wont show it, the line below shows the full traceback for the last resort debug
        # traceback.print_exc()

        sys.exit(1)


# register the hook
sys.meta_path.insert(0, NB_finder())


# Start a watch to check for notebook changes and sync it to its cache file
# Run: `python EasyJupyter.py`
if __name__ == "__main__":

    # TODO tell user about the clean up argument
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="Wipe the cache folder")
    args = parser.parse_args()

    if args.clean:
        cleanup_cache()
        sys.exit(0)

    class NoteBookHandler(FileSystemEventHandler):
        def on_modified(self, event):
            # When notebook is modified
            if (
                event.src_path.endswith(".ipynb")
                and EasyJupyterLoader.SHADOW_DIR not in event.src_path
            ):
                nb_rel_path = os.path.relpath(
                    event.src_path, EasyJupyterLoader.PROJECT_ROOT
                )
                py_cache_filename = os.path.basename(event.src_path).replace(
                    ".ipynb", ".py"
                )
                shadow_path = os.path.join(
                    EasyJupyterLoader.SHADOW_DIR, py_cache_filename
                )

                console.print(
                    f"[default] Changes detected in:[/default] [path]{nb_rel_path}[/path]  | Updating cache at: [path]{shadow_path} [/path]"
                )
                # Sync the notebook and its cache
                loader = EasyJupyterLoader(event.src_path)
                loader.get_code()

    # Initial sync
    sync_all()

    # Start a background process to watch for notebook changes
    observer = Observer()
    observer.schedule(NoteBookHandler(), path=".", recursive=True)
    observer.start()

    console.print(
        Panel(
            "[bold green]👀 EasyJupyter is now watching your project![/bold green]\n"
            "Your cache and IntelliSense will update automatically on save.\n"
            "[dim]Press Ctrl+C to stop the watcher.[/dim]",
            border_style="green",
        )
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
