# Not For You | Dev Notes

- When updating the daemon, we need to clear the old cache and restart the daemon.

    ```bash
    # Graceful stop
    easyjupyter --stop 

    # Or below 3 lines
    pkill -f EasyJupyter.watcher
    rm -rf .easyJupyter_cache
    easyjupyter --sync
    ```

- Setup the development environment:

    ```bash
    # Prerequisites: Install Pipx and Poetry globally
    brew install pipx
    pipx install poetry

    # Create a new conda environment
    conda create -n easyjupyter_env python=3.12 -y
    conda activate easyjupyter_env
    conda install conda-forge::ipykernel -y

    # Link Poetry to the conda environment
    poetry env use $(which python)
    poetry install
    ```

- When developing install the library locally in a environment from the pyproject.toml: `poetry install` or `pip install -e .`
- **Distributing to PyPI:**
  - Releases are automated via GitHub Actions *(CI/CD)*. To publish a new release, tag a commit with the new version number (e.g., `git tag 0.1.2` and `git push --tags`), or do it in Github Desktop.
  - **Note:** If you make any changes to `pyproject.toml` (like adding dependencies), you must run `poetry lock` and commit the updated `poetry.lock` file before tagging the release, otherwise the automated build will fail!
  - **Run:**

    ```bash
        # Ensure your `poetry.lock` is up-to-date, run:
        poetry lock
        # Check for errors:
        poetry check
        # Build the package:
        poetry build
    ```

  - **Testing Before Releasing Locally (on TestPyPI):**
    1. First-Time Setup:
        - Create an API token on TestPyPI. Note: [https://pypi.org/](https://pypi.org/) and [https://test.pypi.org/](https://test.pypi.org/) are not the same, have a different login for each!
        - Configure Poetry with the repository URL and your token:

          ```bash
          # 1. Tell Poetry where TestPyPI is
          poetry config repositories.testpypi https://test.pypi.org/legacy/
          # 2. Provide your token for authentication
          poetry config pypi-token.testpypi <paste-your-testpypi-token-here>
          ```

    2. Manually set the version for the test build, remember to increment it or else it will fail to publish to TestPyPI:

        ```bash
        poetry version 0.1.3
        ```

    3. Run the `Run` bullet point from above.
    4. Publish to TestPyPI:
        - `poetry publish -r testpypi`
