# EasyJupyter

EasyJupyter allows you to seamlessly integrate your Jupyter Notebook code into Python projects or other notebooks. It transforms your notebooks into reusable modules, enabling you to leverage their interactive development environment while maintaining their native display for documentation and collaboration.

Benefits:

- Native GitHub Rendering: Keep your code in notebooks so plots and markdown render natively on GitHub.
- Zero Clutter: Generated cache files are stored in a hidden `.easyJupyter_cache` directory, keeping your workspace clean.
- Custom ignore syntax to ignore exploratory cells, or lines of code.
  
## Ignore Notebook Commands

Use these commands inside your notebooks to control what gets compiled into the cache file.

- **Markdown Cells:** Ignored by default.
- **Ignore An Entire Cell:**
  - Add `# @i-c` to the very top of the cell.
- **Ignore One Line In A Cell:**
  - Add `# @i-l` above the line you want to ignore.

## Getting Started

### Installation & Initial Sync

First, install the library, then run the sync command to generate the cache files for any existing notebooks.

```bash
pip install easyjupyter
easyjupyter --sync
```

### Usage

🚨 In your project's entry point (e.g., main.py), or in a notebook, import the library at the very top of the file:

```python
import EasyJupyter
from my_notebook import Class, Function_name
```

**How It Works:** When EasyJupyter is first imported and run, it initiates a single, detached background daemon. This daemon then continuously monitors your notebooks, instantly updating their hidden cache files every time you save. This design ensures efficient resource use, as only one daemon operates at a time. If the daemon is not already running (e.g., after a system restart or a period of inactivity), a new one will be automatically started when EasyJupyter is imported again.

### Arguments

#### Cache Cleanup

- If you rename, move, or delete a notebook, the old cache file will remain in the hidden cache directory. To clean up the cache, run:

    ```bash
    easyjupyter --clean
    ```

#### Watch Daemon Logs

- If you incorrectly use EasyJupyter in a notebook (e.g., redundant ignore comments), warnings will be added to the cache file of the notebook, so that when you run your program as a whole, the warnings are printed to the console. However, if you are only using notebooks you wont be able to see these warnings, so to view the active warning logs, run:

    ```bash
    easyjupyter --watch
    ```

### VSC Pylance Intellisense Setup

VS Code's Pylance intellisense will not work with notebooks, or the hidden cache files generated for the notebooks. But you can tell it where to look for the cache files. Run one of the following commands in the root of your project:

1. If you don't have a `.vscode/settings.json` file yet, run:

    ```bash
    mkdir -p .vscode && echo '{
        "python.analysis.extraPaths": [
            "./.easyJupyter_cache"
        ]
    }' > .vscode/settings.json
    ```

2. If you already have a `.vscode/settings.json` file, add the following to it:

    ```json
    {
        "python.analysis.extraPaths": [
            "./.easyJupyter_cache"
        ]
    }
    ```

### Other

If any issues occur with the watcher daemon, manually run it with: `python -m EasyJupyter.watcher` (note that this only spawns the daemon in the foreground), or check the logs in `.easyJupyter_cache/watcher.log`.

#### Not For You | Dev Notes

- When updating the daemon, we need to clear the old cache and restart the daemon.

 ```bash
 pkill -f EasyJupyter.watcher
 rm -rf .easyJupyter_cache
 easyjupyter --sync
 ```

- Install locally: `pip install -e .`
- Distributing to PyPI:
  - Releases are automated via GitHub Actions *(CI/CD)*. To publish a new release, tag a commit with the new version number (e.g., `git tag 0.1.2` and `git push --tags`), or do it in Github Desktop.
