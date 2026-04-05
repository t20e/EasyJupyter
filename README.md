# EasyJupyter

🚧🚧🚧🚧🚧🚧🚧🚧 ‼️  Library not ready yet! 🚧🚧🚧🚧🚧🚧🚧🚧

⭐️ This library is specifically for Data Science projects. It is designed so that code is built in Jupyter notebooks, then integrated into main.py.

- For example, if I were building out the Transformer model (from Attention Is All You Need), I'd use notebooks to code out the sub-layers of the model, then use a main.py to integrate all notebooks.

## 💡 Ignore Notebook Commands

- *These lines are skipped when converting from notebook to regular python code. (i.e., they wont run in your final executable)*

- Markdown cells are ignored by default.
    - **#TODO: maybe use `# %%` instead**
- **Ignore an entire cell**:
  - Add `# @i-c` to the very top of the cell.
- **Ignore one line**:
  - Add `# @i-l` above the line you want to ignore.


## How It Is Automated

1. User installs the library
    ```bash
    pip install -e .
    easyjupyter --sync # Start the watcher daemon, only needed once when installing, and every other time you start coding the project. #TODO fix wording
    ```
2. **Use:** They simply put import EasyJupyter at the very top of their main_example.py.
   - The moment they import EasyJupyter, a cache directory is created, and spawns a detached watcher daemon to monitor for notebook changes, which is then synced to  the corresponding cache file.
3. How to make **VSC**'s Pylance intellisense work with EasyJupyter.
    - We need to create a `.vscode/settings.json` file. Use the following commands:

        -# TODO if they have an existing .vscode/settings.json file, this will overwrite it!
        ```bash
        # ⚠️ In the root of your project.
        mkdir -p .vscode && echo '{
            "python.analysis.extraPaths": [
                "./.easyJupyter_cache"
            ]
        }' > .vscode/settings.json
        ```



## Other

- Github rederning
- No file clutter
- Custom ignore syntax

- **#TODO** add info here about the `--cleanup` argument!

- **#TODO** add info here tell user to run the watcher!
