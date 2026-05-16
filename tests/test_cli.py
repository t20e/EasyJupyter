"""Tests CLI commands."""

from easyjupyter.utils import sync_all, cleanup_cache
from easyjupyter.loader import EasyJupyterLoader
from unittest.mock import patch, MagicMock

def test_sync_all_creates_cache(mock_project):
    shadow_dir = mock_project / ".easyJupyter_cache"

    with (
        patch("easyjupyter.loader.PROJECT_ROOT", mock_project),
        patch("easyjupyter.loader.SHADOW_DIR", shadow_dir),
    ):
        sync_all(
            project_root=mock_project,
            shadow_dir=shadow_dir,
            console=MagicMock(),
            updated_notebooks=[],
            loader_class=EasyJupyterLoader,
            force_sync=False
        )

    # Assert cache file was created
    expected_cache_file = shadow_dir / "nested" / "dummy.py"
    assert expected_cache_file.exists()

def test_cleanup_cache_removes_cache(mock_project):
    shadow_dir = mock_project / ".easyJupyter_cache"
    orphan_cache = shadow_dir / "nested" / "deleted_notebook.py"

    # Setup orphan cache file
    orphan_cache.parent.mkdir(parents=True, exist_ok=True)
    orphan_cache.touch()

    cleanup_cache(
        mock_project, shadow_dir=shadow_dir, console=MagicMock()
    )

    # Assert orphan was removed because deleted_notebook.ipynb doesn't exist
    assert not orphan_cache.exists()