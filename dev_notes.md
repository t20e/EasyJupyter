# Not For You | Dev Notes

## Local Development

- When updating the daemon, we need to clear the old cache and restart the daemon.

    ```bash
    # Graceful stop
    easyjupyter --stop 

    # Or below 3 lines
    pkill -f easyJupyter.watcher
    easyjupyter --sync --force
    ```

- Setup the development environment:

    ```bash
    # Prerequisites: Install Pipx and Poetry globally
    brew install pipx
    pipx install poetry

    # Create a new conda environment
    conda create -n easyjupyter_local_test_env python=3.12 -y
    conda activate easyjupyter_local_test_env
    conda install conda-forge::ipykernel -y

    # Tell Poetry  to not create its own environment, and install packages in teh conda environment
    poetry config virtualenvs.create false

    # Link Poetry to the conda environment
    #poetry env use $(which python)
    poetry install
    ```

- When **developing** install the library locally from the pyproject.toml (make sure the env was creating using above commands!):

    ```bash
    # Run from the root of the project
    pip install -e . # Install the packages with the updated local code
    cd example_nested_project
    easyjupyter --stop # Stops the daemon thats running the old version
    # Maybe also reload VSC window that has the nested examples
    easyjupyter --sync --force
    ```

## Distributing to PyPI

### Run Tests First

```bash
pytest
```

### Testing Before Releasing Locally (on TestPyPI)

- First-Time Setup:
  - Create an API token on TestPyPI. Note: [https://pypi.org/](https://pypi.org/) and [https://test.pypi.org/](https://test.pypi.org/) are not the same, have a different login for each!
  - Configure Poetry with the repository URL and your token:

    ```bash
    # 1. Tell Poetry where TestPyPI is
    poetry config repositories.testpypi https://test.pypi.org/legacy/
    # 2. Provide your token for authentication
    poetry config pypi-token.testpypi <paste-your-testpypi-token-here>
    ```

- Publish to TestPyPI:
  - Manually set the version for the test build, remember to increment it or else it will fail to publish to TestPyPI:

    ```bash
    poetry version <example=0.1.3>
    poetry lock
    # Check for errors:
    poetry check
    ```

  - Build the package & publish to TestPyPI:

    ```bash
    poetry build # This is only for local, the Github workflow handles the building when publishing to PyPI
    poetry publish -r testpypi
    ```

### Publishing to PyPI

Releases are automated via GitHub Actions *(CI/CD)*. To publish a new release, tag a commit with the new version number (e.g., `git tag 0.1.2` and `git push --tags`), or do it in Github Desktop.

**Run:**

```bash
    # Ensure your `poetry.lock` is up-to-date, run:
    poetry lock
    # Check for errors:
    poetry check
```

- Then commit and add a tag version, github actions will automatically build and publish the package to PyPI!
