import os
import datetime
from rich.progress import track
from pathlib import Path

from rich.table import Table

auto_cfg_txt = "This file was automatically created by EasyJupyter, so that its daemon knows that this directory is the root of your project. \nIf this is not the root of your project, delete this file and its `.easyJupyter_cache` directory. And add a `.easyJupyterConfig` file to the root of your project."

def get_project_root():
    """
    Traverse up to find the project root by looking for '.easyJupyterConfig' file.
    If it doesn't exist, try to find a '.git' folder or 'pyproject.toml' as a fallback.
    If all fails, return the current directory as the root and create the config.
    """
    original_dir = Path.cwd().resolve()
    current_dir = original_dir
    
    # Pass 1: Look for existing .easyJupyterConfig
    while current_dir.parent != current_dir:
        if (current_dir / ".easyJupyterConfig").exists():
            return current_dir
        current_dir = current_dir.parent
    
    # Pass 2: Fallback to identifying common project roots (.git, pyproject.toml)
    current_dir = original_dir
    while current_dir.parent != current_dir:
        # TODO should I add more project root files here, like makefile?

        if (current_dir / ".git").exists() or (current_dir / "pyproject.toml").exists():
            config_path = current_dir / ".easyJupyterConfig"
            try:
                with open(config_path, "w") as f:
                    f.write(auto_cfg_txt)
            except PermissionError:
                pass  # We found the root, but don't have write access. Just return the path.
            return current_dir
        current_dir = current_dir.parent

    # Pass 3: If all else fails, create it in the directory where the script started
    config_path = original_dir / ".easyJupyterConfig"
    try:
        with open(config_path, "w") as f:
            f.write(auto_cfg_txt)
    except PermissionError:
        pass  # Fallback to returning original_dir even if we can't write the config
    return original_dir


def cleanup_cache(project_root, shadow_dir, console):
    """
    If user moves, renames or deletes a notebook, also delete its cache file.
        Run with: `easyjupyter --clean`
    """
    if not shadow_dir.exists():
        console.print("[yellow]No cache directory found.[/yellow]")
        return

    removed_count = 0

    for root, dirs, files in os.walk(shadow_dir, topdown=False):
        for f in files:
            if f.endswith(".py"):
                cache_file_path = Path(root) / f

                # Reconstruct original notebook path
                rel_to_cache = os.path.relpath(cache_file_path, shadow_dir)
                og_nb_path = project_root / rel_to_cache.replace(".py", ".ipynb")


                if not og_nb_path.exists():
                    os.remove(cache_file_path)
                    console.print(
                        f"[bold red]🗑️  Cache cleared:[/bold red] {rel_to_cache}"
                    )
                    removed_count += 1

        # Clean up empty directories
        if not os.listdir(root) and Path(root) != shadow_dir:
            os.rmdir(root)

    if removed_count > 0:
        console.print(
            f"[bold green]Cache cleaned:[/bold green] {removed_count} files removed."
        )
    else:
        console.print("[yellow]Cache is okay, no need to clean.[/yellow]")


def _render_table(output_console, updated_notebooks):
    table = Table(
        title="Notebook Updates",
        title_style="label",
        show_header=True,
        header_style="bold default",
    )
    table.add_column("Notebook File Updated", style="path", width=45)
    table.add_column("Cache Updated At", style="cell_location", width=45)

    for nb_rel_path, shadow_path in updated_notebooks:
        table.add_row(nb_rel_path, shadow_path)

    output_console.print(table)


def print_nb_update_report(shadow_dir, console, updated_notebooks):
    if not updated_notebooks:
        return

    # Check if we should write to a log file instead of terminal
    # We can detect the daemon by checking if our PID matches the watcher.pid file
    log_path = shadow_dir / "watcher.log"

    # If the log file exists and we are likely the daemon, log to file
    # Otherwise, if it's a manual sync or main script, print to console.
    # For the log file, we'll use a plain text format.
    if log_path.exists():
        with open(log_path, "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n[{timestamp}] Notebook Updates:\n")
            for nb_rel_path, shadow_path in updated_notebooks:
                f.write(f"  - Notebook: {nb_rel_path}\n")
                f.write(f"    Cache:    {shadow_path}\n")
            f.write("\n")
    else:
        _render_table(console, updated_notebooks)


def sync_all(project_root, shadow_dir, console, updated_notebooks, loader_class):
    """
    When user updates a Notebook sync it to its cache file.
    """
    root_dir = project_root
    updated_notebooks.clear()  # clear list in-place to affect the global instance
    all_nb = []

    for root, _, files in os.walk(root_dir):
        if str(shadow_dir) in root:
            continue  # skip the cache dir
        all_nb.extend([
            # os.path.join(root, f) for f in files if f.endswith(".ipynb")
            Path(root) / f for f in files if f.endswith(".ipynb")
            ])

    if all_nb:
        for nb_path in track(all_nb, description="[cyan]Syncing Notebooks..."):
            # Create a loader instance for each notebook to trigger the sync
            loader = loader_class(nb_path)
            loader.get_code()
        console.print("[bold green]Sync Complete![/bold green]")
    else:
        console.print("[yellow]No notebooks updated![/yellow]")

    print_nb_update_report(shadow_dir, console, updated_notebooks)


def stop_daemon(shadow_dir, console):
    """Stops the background daemon process gracefully using its PID lock file."""
    import signal
    pid_file = shadow_dir / "watcher.pid"
    
    if not pid_file.exists():
        console.print("[yellow]Watcher daemon is not currently running.[/yellow]")
        return

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        
        # Send termination signal to the background process
        os.kill(pid, signal.SIGTERM)
        os.remove(pid_file)
        console.print(f"[bold green]Watcher daemon (PID {pid}) stopped successfully.[/bold green]")
    except ProcessLookupError:
        os.remove(pid_file)
        console.print("[yellow]Daemon process not found. Cleaned up stale PID file.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Failed to stop daemon:[/bold red] {e}")
