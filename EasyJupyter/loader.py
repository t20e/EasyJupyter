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
import shutil
import argparse
from rich.progress import track

VSC_SETTINGS_UPDATED = False
UPDATED_NOTEBOOKS = []  # Track what notebooks the user has updated


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


def sync_all():
    """
    When user updates a Notebook sync it to its cache file.
    """
    global UPDATED_NOTEBOOKS
    root_dir = "."
    UPDATED_NOTEBOOKS = []  # clear list
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
    PROJECT_ROOT = os.getcwd()
    SHADOW_DIR = os.path.join(PROJECT_ROOT, ".easyJupyter_cache")

    def __init__(self, path):
        self.path = path

    def _get_shadow_path(self):
        """Mirrors the source directory structure into the cache directory."""
        rel_path = os.path.relpath(self.path, self.PROJECT_ROOT)
        shadow_rel = rel_path.replace(".ipynb", ".py")
        return os.path.join(self.SHADOW_DIR, shadow_rel)

    def create_module(self, spec):
        """Import the notebook as a module"""
        return types.ModuleType(spec.name)

    def exec_module(self, module):
        # if the file is 'models/layers/attention.ipynb', we want the package to be 'models.layers'
        path_parts = os.path.normpath(self.path).split(os.sep)
        # remove extension and join with '.'
        rel_path = os.path.relpath(self.path, self.PROJECT_ROOT)
        package_parts = os.path.dirname(rel_path).split(os.sep)
        pkg_path = ".".join([p for p in package_parts if p])

        # Set the attributes
        module.__file__ = os.path.abspath(self.path)
        module.__package__ = pkg_path

        # Execute with code in the module's namespace
        code = self.get_code()

        try:
            exec(code, module.__dict__)
        except Exception as e:
            self.report_notebook_error(e)

    def get_code(self):
        """Returns code from cache if it has not been updated since"""
        shadow_path = self._get_shadow_path()

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
        """Create a shadow Python file to store the transformed contents of a notebook."""
        shadow_path = self._get_shadow_path()
        os.makedirs(os.path.dirname(shadow_path), exist_ok=True)

        # Write the shadow file
        with open(shadow_path, "w") as f:
            f.write(code)

        # Print to show what notebooks were updated
        nb_rel_path = os.path.relpath(self.path, self.PROJECT_ROOT)
        shadow_rel_path = os.path.relpath(shadow_path, self.PROJECT_ROOT)

        # TODO call update here
        UPDATED_NOTEBOOKS.append((nb_rel_path, shadow_rel_path))

    def transform_notebook(self):
        """
        Parse a notebook into its shadow Python cache file. The notebook comes as JSON and apply ignore syntax.
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
