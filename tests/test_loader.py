"""Tests notebook parsing and ignore syntax"""

from easyjupyter.loader import EasyJupyterLoader
from unittest.mock import patch
import os


def test_transform_notebook_ignore_syntax(mock_project):
    """Verify that def transform_notebook logic correctly applied the ignore syntaxes"""
    nb_path = mock_project / "nested" / "dummy.ipynb"

    # Use the temp directory
    with (
        patch("easyjupyter.loader.PROJECT_ROOT", mock_project),
        patch("easyjupyter.loader.SHADOW_DIR", mock_project / ".easyJupyter_cache"),
    ):
        loader = EasyJupyterLoader(str(nb_path))
        code = loader.transform_notebook()

        # Assert the valid code is present
        assert "def hello():" in code
        assert "return 'Hello, world!'" in code

        # Assert the ignored cell is commented out
        assert "# [Ignored Cell] def ignored_func():" in code

        # Remove the correctly commented out line, then check if the raw code exists anywhere else
        assert "def ignored_func():" not in code.replace("# [Ignored Cell] def ignored_func():", "")

        # Assert the ignored line is commented out
        assert "# [Skip Line] print('Line should be ignored')" in code
        