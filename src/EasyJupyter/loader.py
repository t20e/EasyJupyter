import types
import nbformat
import sys
import os
import sys
import importlib.abc
import importlib.util
import traceback
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from rich.table import Table
import json
import time
from rich.progress import track
import datetime

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


def cleanup_cache():
    """
    If user moves, renames or deletes a notebook, also delete its cache file.
        Run with: `easyjupyter --clean`
    """
    if not os.path.exists(EasyJupyterLoader.SHADOW_DIR):
        console.print("[yellow]No cache directory found.[/yellow]")
        return

    removed_count = 0

    for root, dirs, files in os.walk(EasyJupyterLoader.SHADOW_DIR, topdown=False):
        for f in files:
            if f.endswith(".py"):
                cache_file_path = os.path.join(root, f)

                # Reconstruct original notebook path
                rel_to_cache = os.path.relpath(
                    cache_file_path, EasyJupyterLoader.SHADOW_DIR
                )
                og_nb_path = os.path.join(
                    EasyJupyterLoader.PROJECT_ROOT,
                    rel_to_cache.replace(".py", ".ipynb"),
                )

                if not os.path.exists(og_nb_path):
                    os.remove(cache_file_path)
                    console.print(
                        f"[bold red]🗑️  Cache cleared:[/bold red] {rel_to_cache}"
                    )
                    removed_count += 1

        # Clean up empty directories
        if not os.listdir(root) and root != EasyJupyterLoader.SHADOW_DIR:
            os.rmdir(root)

    if removed_count > 0:
        console.print(
            f"[bold green]Cache cleaned:[/bold green] {removed_count} files removed."
        )
    else:
        console.print("[yellow]Cache is okay, no need to clean.[/yellow]")


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

    print_nb_update_report()


def print_nb_update_report():
    if not UPDATED_NOTEBOOKS:
        return

    # Check if we should write to a log file instead of terminal
    # We can detect the daemon by checking if our PID matches the watcher.pid file
    log_path = os.path.join(EasyJupyterLoader.SHADOW_DIR, "watcher.log")

    # If the log file exists and we are likely the daemon, log to file
    # Otherwise, if it's a manual sync or main script, print to console.
    # For the log file, we'll use a plain text format.
    if os.path.exists(log_path):
        with open(log_path, "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n[{timestamp}] Notebook Updates:\n")
            for nb_rel_path, shadow_path in UPDATED_NOTEBOOKS:
                f.write(f"  - Notebook: {nb_rel_path}\n")
                f.write(f"    Cache:    {shadow_path}\n")
            f.write("\n")
    else:
        _render_table(console)


def _render_table(output_console):
    table = Table(
        title="Notebook Updates",
        title_style="label",
        show_header=True,
        header_style="bold default",
    )
    table.add_column("Notebook File Updated", style="path", width=45)
    table.add_column("Cache Updated At", style="cell_location", width=45)

    for nb_rel_path, shadow_path in UPDATED_NOTEBOOKS:
        table.add_row(nb_rel_path, shadow_path)

    output_console.print(table)


class NB_finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        # Look for the notebook ile in the expected path
        mod_name = fullname.split(".")[-1]

        # Use python's native sys.path for top-level imports
        search_paths = path or sys.path

        # Search for the notebook
        for p in search_paths:

            # When importing `import EasyJupyter` in a notebook, IPython/Jupyter uses an empty string ("") to denote the current working directory
            if p == "":
                p = os.getcwd()

            # Ensure the path is valid string/directory no zip files
            if not isinstance(p, str) or not os.path.isdir(p):
                continue

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

        UPDATED_NOTEBOOKS.append((nb_rel_path, shadow_rel_path))

    def transform_notebook(self):
        """
        Parse a notebook into its shadow Python cache file. The notebook comes as JSON and apply ignore syntax. Handles OS write locks/race conditions.
        """

        max_retries = 5
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                with open(self.path, "r") as f:
                    contents = f.read()
                    if not contents.strip():
                        # File is empty, wait and try again
                        time.sleep(retry_delay)
                        continue

                    notebook = nbformat.reads(contents, as_version=4)
                    break  # success
            except (nbformat.reader.NotJSONError, json.JSONDecodeError):
                # File is not JSON, wait and try again
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise  # Re-raise if it still fails after max retries
        else:
            # This executes if the loop finishes without raising 'break'
            raise Exception(
                f"Failed to read notebook: {self.path} after {max_retries} attempts."
            )

        nb_cells = notebook["cells"]
        nb_metadata = notebook["metadata"]
        nb_format = notebook["nbformat"]
        nb_nbformat_minor = notebook["nbformat_minor"]

        # Warnings to tell user if they used a skip line syntax but it has an empty line below it, or other warnings
        warnings = []

        # Extract code to execute from the notebook
        exec_code_extract = []

        for cell_idx, cell in enumerate(nb_cells):
            lines = cell.source.splitlines()

            # Start each cell with a header comment for dev, makes the "shadow file" readable and help VSC search
            exec_code_extract.append(f"# {'='*64}")
            exec_code_extract.append(f"# CELL {cell_idx} | ID: {cell.id}")
            exec_code_extract.append(f"# {'='*64}")

            # --- Warning detection for IGNORE_CELL_SYNTAX ---
            ignore_cell_syntax_count = 0
            ignore_line_syntax_count = 0
            first_ignore_cell_line = -1

            for line_idx, line in enumerate(lines):
                clean_line = line.strip()
                if clean_line.startswith(self.IGNORE_CELL_SYNTAX):
                    ignore_cell_syntax_count += 1
                    if first_ignore_cell_line == -1:
                        first_ignore_cell_line = line_idx
                elif clean_line.startswith(self.IGNORE_LINE):
                    ignore_line_syntax_count += 1

            if ignore_cell_syntax_count > 1:
                warnings.append(
                    f"Cell {cell_idx}: Redundant '{self.IGNORE_CELL_SYNTAX}' stacked."
                )

            if ignore_cell_syntax_count > 0:
                for i in range(first_ignore_cell_line):
                    if lines[i].strip() != "":
                        warnings.append(
                            f"Cell {cell_idx}: '{self.IGNORE_CELL_SYNTAX}' is not at the very top of the cell. The entire cell will still be ignored."
                        )
                        break

                if ignore_line_syntax_count > 0:
                    warnings.append(
                        f"Cell {cell_idx}: Contains both '{self.IGNORE_CELL_SYNTAX}' and '{self.IGNORE_LINE}'. The line ignore is redundant since the entire cell is ignored."
                    )
            # --- End warning detection ---

            # --- Cell processing logic ---
            if cell.cell_type != "code" or ignore_cell_syntax_count > 0:
                # If it's a markdown cell or an ignored code cell
                for line in lines:
                    exec_code_extract.append(f"# [Ignored Cell] {line}")
            else:
                # Process lines
                skip_next = False
                for line_idx, line in enumerate(lines):
                    clean = line.strip()

                    # If this line is a trigger, comment it out and prepare to skip the next line
                    if clean.startswith(self.IGNORE_LINE):
                        if skip_next:
                            warnings.append(
                                f"Cell {cell_idx} (0-indexed) line {line_idx+1}: Redundant '{self.IGNORE_LINE}' stacked."
                            )
                        exec_code_extract.append(f"# {line}")
                        skip_next = True
                        continue  # Move to next line

                    # If skip_next is active, comment this line out and reset skip, this is to catch redundant skip lines stacked on top of each other
                    elif skip_next:
                        if clean == "":
                            warnings.append(
                                f"Cell {cell_idx} (0-indexed) line {line_idx+1}: '{self.IGNORE_LINE}' used before an empty line."
                            )
                        exec_code_extract.append(f"# [skip line] {line}")
                        skip_next = False
                    else:  # Regular code to execute line
                        exec_code_extract.append(line)

                # Check if the cell ended with a skip trigger but had no code to actually skip
                if skip_next:
                    warnings.append(
                        f"Cell {cell_idx} (0-indexed): '{self.IGNORE_LINE}' used at the end of the cell with no code to skip."
                    )

            exec_code_extract.append("")  # Add a next line

        # Inject warnings into the generated code so the user sees them when executing
        if warnings:
            warning_imports = ["import warnings"]
            warning_imports.append(
                f'print("\\n\\n🚨🚨🚨 Incorrect use of EasyJupyter, warnings listed below, remember to fix the warnings below in the notebook, and not in this file!\\n\\n")'
            )

            for w in warnings:
                safe_w = w.replace('"', '\\"')
                warning_imports.append(
                    f'warnings.warn("EasyJupyter: {safe_w}\\n", UserWarning)'
                )
                # Also write to watcher.log
                print(f"[WARNING] {os.path.basename(self.path)} - {w}")

            exec_code_extract = warning_imports + [""] + exec_code_extract

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

        sys.exit(1)
