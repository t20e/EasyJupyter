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

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme


IGNORE_CELL_SYNTAX = "# @i-c"
IGNORE_LINE = "# @i-l"
PROJECT_ROOT = os.path.abspath(os.curdir)
SHADOW_DIR = ".easyJupyter_cache"


# Rich library theme
custom_theme = Theme({"label": "bold default", "path": "cyan", "location": "yellow"})
console = Console(theme=custom_theme)


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
    def __init__(self, path):
        self.path = path

    def create_module(self, spec):
        """Import the notebook as a module"""
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
        shadow_path = os.path.join(SHADOW_DIR, f"shadow_{py_cache_filename}")

        if not os.path.exists(SHADOW_DIR):  # Ensure cache dir exists
            os.makedirs(SHADOW_DIR)

        # Check timestamps
        if os.path.exists(shadow_path):
            nb_mtime = os.path.getmtime(self.path)
            shadow_mtime = os.path.getmtime(shadow_path)

            if shadow_mtime > nb_mtime:
                # Cache is fresh, read and return it
                with open(shadow_path, "r") as f:
                    return f.read()

        # Else notebook was updated, re-transform it and save to cache
        return self.transform_notebook(shadow_path)

    def write_shadow_ref(self, code):
        """Create a shadow_{notebook_filename} to store the transformed contents of a notebook"""

        # Ensure hidden cache dir exists
        if not os.path.exists(SHADOW_DIR):
            os.makedirs(SHADOW_DIR)

        py_cache_filename = os.path.basename(self.path).replace(".ipynb", ".py")
        shadow_path = os.path.join(SHADOW_DIR, f"shadow_{py_cache_filename}")

        # Write the shadow file
        with open(shadow_path, "w") as f:
            f.write(code)

        print("Updated cache with new code!")

    def transform_notebook(self, shadow_path):
        """
        Parse a notebook: Comes as JSON and apply ignore syntax.

        Args:
            shadow_path: Absolute path to the shadow cache of the notebook
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
            exec_code_extract.append(f"# {'='*40}")
            exec_code_extract.append(f"# CELL {cell_idx} | ID: {cell.id}")
            exec_code_extract.append(f"# {'='*40}")

            if cell.cell_type != "code" or any(
                l.strip().startswith(IGNORE_CELL_SYNTAX) for l in lines
            ):
                for line in lines:
                    exec_code_extract.append(f"# [Ignored Cell] {line}")
            else:
                # Process lines
                skip_next = False
                for line in lines:
                    clean = line.strip()

                    # If this line is a trigger, comment it out and prepare to skip the next line
                    if clean.startswith(IGNORE_LINE):
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
        shadow_path = os.path.join(SHADOW_DIR, f"shadow_{py_cache_filename}")

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
            f"[label]Location:[/label] [location]{target_cell}[/location]\n"
            f"[label]Code:[/label] {all_lines[line_no-1].strip()}"
        )

        console.print(
            Panel(
                error_message,
                title=f"[bold red]EasyJupyter Error: {type(error).__name__}[/bold red]",
                border_style="red",
            )
        )

        # print("\n" + "=" * 50)
        # print(f"EASYJUPYTER ERROR")
        # print(f"Notebook: {os.path.basename(self.path)}")
        # print(f"Location (0-indexing): {target_cell}")
        # print(f"Error: {type(error).__name__}: {error}")

        # if all_lines and line_no <= len(all_lines):
        #     print(f"Code: {all_lines[line_no-1].strip()}")

        # print("=" * 50)

        # TODO: Add a verbose flag, for example if the error occured in Pytorch, my error above wont show it, the line below shows the full traceback for the last resort debug
        # traceback.print_exc()

        sys.exit(1)


# register the hook
sys.meta_path.insert(0, NB_finder())
