"""Pytest (setup/teardown) fixtures."""

import pytest
import tempfile
import json
from pathlib import Path
import sys


@pytest.fixture
def mock_project():
    """Creates an isolated temporary project directory simulating a user's project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create a .easyJupyterConfig file
        (root / ".easyJupyterConfig").touch()

        nested = root / "nested"
        nested.mkdir()

        # Create a dummy notebook
        nb_path = nested / "dummy.ipynb"
        notebook_data = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": [
                        "def hello():\n",
                        "    return 'Hello, world!'\n",
                    ],
                    "metadata": {},
                    "outputs": [],
                    "execution_count": 1,
                },
                {
                    "cell_type": "code",
                    "source": [
                        "# @i-c\n",  # Ignore cell test
                        "def ignored_func():\n",
                        "    pass\n",
                    ],
                    "metadata": {},
                    "outputs": [],
                    "execution_count": 2,
                },
                {
                    "cell_type": "code",
                    "source": [
                        "# @i-l\n",  # Ignore line test
                        "print('Line should be ignored')\n",
                    ],
                    "metadata": {},
                    "outputs": [],
                    "execution_count": 1,
                },
            ],
            "metadata": {}, "nbformat": 4, "nbformat_minor": 2
        }

        nb_path.write_text(json.dumps(notebook_data))

        yield root

        # Teardown: Clean up sys.modules and sys.meta_path if tests modified them
        to_remove = [mod for mod in sys.modules if mod.startswith("nested")]
        for mod in to_remove:
            del sys.modules[mod]
