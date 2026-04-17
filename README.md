# EasyJupyter

EasyJupyter allows you to effortlessly integrate your Jupyter Notebook code into any Python project or other notebooks. It intelligently transforms your notebooks into standard Python modules, allowing you to import functions, classes, and variables as if they were regular `.py` files. This seamless process, managed by a background caching mechanism, lets you leverage the interactive development environment of notebooks for rapid prototyping and analysis, while ensuring your code is modular and reusable.

This is particularly useful for AI/Data science projects. For example, if you are building out a Transformer architecture, you could code and write notes for each layer of the model in its own notebook, and then seamlessly import them into your main project or another notebook.

Key Benefits:

- Native GitHub Rendering: Keep your code in notebooks so plots and markdown render natively on GitHub.
- Zero Clutter: Generated cache files are stored in a hidden `.easyJupyter_cache` directory, keeping your workspace clean.
- Custom ignore syntax to ignore exploratory cells, or lines of code.

**How It Works:** When EasyJupyter is first imported within a project, it initiates a single, detached background daemon for that specific project. This daemon is tied to your project's root (specifically, the generated `.easyJupyter_cache/watcher.pid` file) and monitors only the notebooks within it. This per-project design ensures that different projects can have their own daemons completely isolated and do not interfere with each other. If the daemon for a project is not already running, it will be started automatically the next time you import EasyJupyter within that project's environment.

## Table of Contents

- [EasyJupyter](#easyjupyter)
  - [Table of Contents](#table-of-contents)
  - [Ignore Notebook Commands](#ignore-notebook-commands)
  - [Getting Started](#getting-started)
    - [Installation](#installation)
    - [Usage](#usage)
    - [Arguments](#arguments)
      - [Sync All Notebooks](#sync-all-notebooks)
      - [Cache Cleanup](#cache-cleanup)
      - [Watch Daemon Logs](#watch-daemon-logs)
      - [Stop Daemon](#stop-daemon)
    - [VSC Pylance Intellisense Setup](#vsc-pylance-intellisense-setup)
    - [Resolving Errors](#resolving-errors)

## Ignore Notebook Commands

Use these commands inside notebooks to control what gets compiled into the cache.

- **Markdown Cells:** Ignored by default.
- **Ignore An Entire Cell:**
  - Add `# @i-c` to the very top of the cell.
- **Ignore One Line In A Cell:**
  - Add `# @i-l` above the line you want to ignore.

## Getting Started

### Installation

```bash
pip install easyjupyter
```

### Usage

In your project's entry point (e.g., `main.py`) and in any Jupyter Notebooks where you want the daemon to be active or when importing from other notebooks, import the library at the very top of the file:

```python
import EasyJupyter # Import at the very top of the file
from my_notebook import Class, Function_name
```

- Importing EasyJupyter in many files is not a problem, as only one daemon can run at a time per project, you could import it in all your files if you want.

> [!important]
> Never edit the cache files directly, only edit the notebooks!
>
> If your project has nested folders. Create a `easyJupyterConfig` file in the root of your project!
>
> ```bash
> # cd into your project root
> touch easyJupyterConfig 
> echo "EasyJupyter, so that its daemon knows that this directory is the root of your project." > easyJupyterConfig
> ```

---

> [!NOTE]
>
> - Check out [example_nested_project](https://github.com/t20e/EasyJupyter/tree/main/example_nested_project). Note run `main.py` from inside ./example_nested_project, also for VSC's Pylance to kick in, open a new VSC window with ./example_nested_project as root, and follow VSC Pylance Intellisense Setup below.
>
> - You should use Notebook automatic reloading if you are simultaneously working with many notebooks that import each other. Add the following to a cell at the top of notebooks!
>
>   ```python
>   # @i-c
>   %load_ext autoreload
>   %autoreload 2
>   ```

### Arguments

- Always run `easyjupyter --<argument>` from somewhere in a project, where the daemon lives.

#### Sync All Notebooks

- Sync all notebooks to the cache, run:
  - Do this only if your cache is empty and you have existing notebooks, not every time you update a notebook.

    ```bash
    easyjupyter --sync
    ```

#### Cache Cleanup

- If you rename, move, or delete a notebook, the old cache file will remain in the hidden cache directory. To clean up the cache, run:

    ```bash
    easyjupyter --clean
    ```

#### Watch Daemon Logs

- If you incorrectly use EasyJupyter in a notebook (e.g., redundant ignore comments), warnings will be embedded directly into the generated cache file. These warnings will be printed to the console (or notebook output) whenever the cached module is imported and executed, even when importing from another notebook. However, if you want to view the live warnings as the daemon runs, run:

    ```bash
    easyjupyter --watch
    ```

#### Stop Daemon

- The daemon process will terminate by itself, however, if you need to gracefully stop the background daemon process, run:

    ```bash
    easyjupyter --stop
    ```

### VSC Pylance Intellisense Setup

VS Code's Pylance intellisense will not natively work with notebooks, or the hidden cache files generated for the notebooks. But you can tell it where to look for the cache files. Run one of the following commands in the root of your project:

1. If you don't have a `.vscode/settings.json` file yet, run:

    ```bash
    mkdir -p .vscode && echo '{
        "python.analysis.extraPaths": [
            "./.easyJupyter_cache"
        ]
    }' > .vscode/settings.json
    ```

2. If you already have a `.vscode/settings.json` file, add the following inside the `{}` brackets:

    ```json
    "python.analysis.extraPaths": [
        "./.easyJupyter_cache"
    ]
    ```

3. Make sure that in VSC you are selecting the environment that has EasyJupyter installed. For notebooks, VSC will prompt you to select the environment when you run a cell in a notebook. For .py files, you can manually select the environment in the bottom right corner of VSC.

### Resolving Errors

If any issues occur with the watcher daemon, manually run it with: `python -m EasyJupyter.watcher` (note that this spawns the daemon in the foreground for debugging). If the daemon is already running in the background, you will need to delete the `.easyJupyter_cache/watcher.pid` file first.

You can always check the background daemon logs inside `.easyJupyter_cache/watcher.log`.
