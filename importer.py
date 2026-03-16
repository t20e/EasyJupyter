import nbformat
import sys
from types import ModuleType
import os


IGNORE_CELL_SYNTAX = "# @i-c"
IGNORE_LINE = "# @i-l"
PROJECT_ROOT = os.path.abspath(os.curdir)


# def import_notebook(path):
    # """
    # Import a notebook and convert its code into a python script.

    # Args:
    #     path: Absolute path to the notebook
    # """
    # with open(path, "r") as f:
    #     notebook = nbformat.read(f, as_version=4)

    # nb_cells = notebook["cells"]
    # nb_metadata = notebook["metadata"]
    # nb_format = notebook["nbformat"]
    # nb_nbformat_minor = notebook["nbformat_minor"]

    # # Warnings to tell user if they used a skip line syntax but it has an empty line below it, or other warnings
    # # TODO add all warnings checks possible
    # warnings = []

    # # Extract code to execute from the notebook
    # code_to_exec = ""

    # for cell_idx, cell_val in enumerate(nb_cells):
    #     if cell_val.cell_type == "code" and cell_val.source.strip():
    #         lines = cell_val.source.split("\n")

    #         # === Filter out cells that the user has marked as exploratory or ignore lines or cells
    #         # 1. Ignore entire cell
    #         if any(l.strip().startswith(IGNORE_CELL_SYNTAX) for l in lines):
    #             continue

    #         # 2. Ignore single lines
    #         filtered_lines = []
    #         skip_next = False

    #         for idx, line in enumerate(lines):
    #             clean_line = line.strip()  # If the line is indented like `     #%L`

    #             # Handle first ignore line
    #             if skip_next:
    #                 skip_next = False
    #                 # Warning check: If the line we are skipping is also a trigger.
    #                 if clean_line.startswith(IGNORE_LINE):
    #                     context = cell_val.source.strip()[:30].replace("\n", " ")
    #                     # TODO add warning information, so user can easily find the cell.
    #                     warnings.append(
    #                         {
    #                             "type": "Redundant ignore syntax",
    #                             "cell_index": cell_idx,
    #                             "line_number": idx + 1,
    #                             "Context": f"'{context}...",
    #                         }
    #                     )
    #                     skip_next = True  # Keep skipping for the next actual line
    #                 continue

    #             if clean_line.startswith(IGNORE_LINE):
    #                 # Check if this line is the last line of the cell
    #                 if idx == len(lines) - 1:
    #                     context = cell_val.source.strip()[:30].replace("\n", " ")
    #                     warnings.append(
    #                         {
    #                             "type": "Dangling syntax",
    #                             "cell_index": cell_idx,
    #                             "line_number": idx + 1,
    #                             "Context": f"'{context}...",
    #                         }
    #                     )
    #                 skip_next = True
    #                 continue

    #             filtered_lines.append(line)

    #         code_to_exec += "\n".join(filtered_lines) + "\n\n"

    # print(code_to_exec)
    # print("EasyJupyter Warnings", warnings)
    # # exec(code_to_exec, mod.__dict__)
    # # return mod

def import_notebook(path):
    with open(path, "r") as f:
        notebook = nbformat.read(f, as_version=4)

    # We track the "Global Line Number" to help the user find things
    code_to_exec = []
    
    for cell_idx, cell in enumerate(notebook["cells"]):
        lines = cell.source.splitlines()
        
        # 1. Start each cell with a header comment for the developer
        # This makes the "Shadow File" readable and helps VSC search
        code_to_exec.append(f"# --- CELL {cell_idx} ID: {cell.id} ---")
        
        if cell.cell_type != "code":
            # Map Markdown to comments so line count stays the same
            for line in lines:
                code_to_exec.append(f"# [Markdown] {line}")
            continue

        # 2. Check for Cell-level ignore
        if any(l.strip().startswith(IGNORE_CELL_SYNTAX) for l in lines):
            for line in lines:
                code_to_exec.append(f"# [Ignored Cell] {line}")
            continue

        # 3. Process Lines
        skip_next = False
        for line_idx, line in enumerate(lines):
            clean = line.strip()
            
            if skip_next:
                # IMPORTANT: Don't 'continue', append a commented version
                code_to_exec.append(f"# [Ignored Line] {line}")
                skip_next = False
                continue

            if clean.startswith(IGNORE_LINE):
                code_to_exec.append(f"# {line}") # Keep the trigger comment
                skip_next = True
                continue

            code_to_exec.append(line)

    print(code_to_exec)
    # return "\n".join(code_to_exec)

import_notebook(f"{PROJECT_ROOT}/test_example.ipynb")
