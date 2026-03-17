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

IGNORE_CELL_SYNTAX = "# @i-c"
IGNORE_LINE = "# @i-l"
PROJECT_ROOT = os.path.abspath(os.curdir)
SHADOW_DIR = ".easyJupyter_cache"


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
        # Transform notebook and ignore syntaxes
        code = self.transform_notebook()

        # Create an aesthetic only shadow file
        self.write_shadow_ref(code)  # TODO

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

    def transform_notebook(self):
        """
        Import a notebook and convert its code into a python script.

        Args:
            path: Absolute path to the notebook
        """

        path = self.path

        with open(path, "r") as f:
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

            # exec_code_extract.append(f"# --- CELL {cell_idx} ID: {cell.id} ---")

            if cell.cell_type != "code":
                # Map Markdown cells
                for line in lines:
                    exec_code_extract.append(f"# [Markdown] {line}")
                continue
            elif any(l.strip().startswith(IGNORE_CELL_SYNTAX) for l in lines):
                # Check for ignore whole code cell syntax
                for line in lines:
                    exec_code_extract.append(f"# [Ignored Cell] {line}")
            else:
                # Process lines
                skip_next = False
                for line_idx, line in enumerate(lines):
                    clean = line.strip()

                    if skip_next:
                        exec_code_extract.append(f"# [skip line] {line}")
                        skip_next = False
                        continue

                    if clean.startswith(IGNORE_LINE):
                        exec_code_extract.append(
                            f"# {line}"
                        )  # Keep the trigger comment
                        skip_next = True
                        continue

                    exec_code_extract.append(line)

            # Add a newline after every cell
            exec_code_extract.append("")

        # Return final code to exec
        return "\n".join(exec_code_extract)

    def report_notebook_error(self, error):
        # Extract the traceback info
        etype, evalue, tb = sys.exc_info()

        stack = traceback.extract_tb(tb) # returns a list of FrameSummary objects

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
        print("\n" + "=" * 50)
        print(f"EASYJUPYTER ERROR")
        print(f"Notebook: {os.path.basename(self.path)}")
        print(f"Location: {target_cell}")
        print(f"Error: {type(error).__name__}: {error}")

        if all_lines and line_no <= len(all_lines):
            print(f"Code: {all_lines[line_no-1].strip()}")
            
        print("=" * 50)

        # # Still show the full traceback for the last resort debug
        # traceback.print_exc()

        sys.exit(1)


# register the hook
sys.meta_path.insert(0, NB_finder())
