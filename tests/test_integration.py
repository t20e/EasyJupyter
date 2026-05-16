"""Tests the import hook and daemon."""

import subprocess
import sys


def test_end_to_end_import(mock_project):
    # Create a main.py  in the mock project
    main_py = mock_project / "main.py"
    main_py.write_text(
        "import easyjupyter\n" "from nested.dummy import hello\n" "print(hello())\n"
    )

    result = subprocess.run(
        [sys.executable, str(main_py)],
        cwd=mock_project,
        capture_output=True,
        text=True,
    )

    # Assert successful execution and daemon spawn
    assert result.returncode == 0
    assert "Hello, world!" in result.stdout

    # Cleanup the detached daemon spawned by the subprocess
    subprocess.run(
        [sys.executable, "-m", "easyjupyter.cli", "--stop"], cwd=str(mock_project)
    )
