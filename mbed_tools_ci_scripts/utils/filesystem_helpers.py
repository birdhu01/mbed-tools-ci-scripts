"""Helpers with regards to actions on the filesystem."""
import os
import tempfile
import shutil
import platform
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Iterator, Generator, Callable, Any

logger = logging.getLogger(__name__)


@contextmanager
def cd(new_dir: str) -> Generator:
    """Context manager allowing an operation to be performed inside given directory.

    Args:
         new_dir: the directory to move into

    """
    prev_dir = os.getcwd()
    os.chdir(os.path.expanduser(new_dir))
    try:
        yield
    finally:
        os.chdir(prev_dir)


def walk_up_tree_to_root(starting_point: str) -> Iterator[str]:
    """Iterates from path to root.

    Args:
        starting_point: path from where to start.

    Returns:
        Iterator walking up the directory tree up to the root.
    """
    if not os.path.exists(starting_point):
        raise FileNotFoundError(starting_point)

    current_dir = os.path.realpath(
        starting_point if os.path.isdir(starting_point) else os.path.dirname(
            starting_point))

    previous_dir = None
    while previous_dir != current_dir:
        yield current_dir
        previous_dir = current_dir
        current_dir = os.path.dirname(current_dir)


def _get_directory_walk_method(top: bool) -> Callable[[str], Iterator[str]]:
    def walk_down_tree(start: str) -> Iterator[str]:
        for root, dirs, files in os.walk(start, followlinks=True):
            yield root

    return walk_up_tree_to_root if top else walk_down_tree


def find_file_in_tree(file_name: str,
                      starting_point: str = os.getcwd(),
                      top: bool = False) -> str:
    """Finds a file in directory tree.

    Args:
        file_name: name of the file to look for.
        starting_point: path from where to start the search
        top: search up the directory tree to root if True; down the tree otherwise.

    Returns:
            path of the file of interest.
    """
    if not file_name:
        raise ValueError('Undefined file name')

    iterator = _get_directory_walk_method(top)
    for directory in iterator(starting_point):
        file_path = os.path.join(directory, file_name)
        if os.path.exists(file_path):
            break
    else:
        raise FileNotFoundError(
            f'File [{file_name}] not found anywhere in directories {"above" if top else "under"} {starting_point}'
        )
    return file_path


class TemporaryDirectory:
    """Creates and returns a temporary directory.

    This is the same as tempfile.TemporaryDirectory in most cases.
    However, on CI the temporary folder may not be accessible.
    Moreover, on Windows TemporaryDirectory will fail cleaning up
    (https://bugs.python.org/issue22107) and hence, a workaround had to be
    implemented.

    """

    def __init__(self) -> None:
        """Constructor."""
        self._tmp_dir_context_manager = tempfile.TemporaryDirectory()
        self._tmp_dir_path = Path(self._tmp_dir_context_manager.name).resolve()

    @property
    def path(self) -> Path:
        """Path to the folder."""
        return self._tmp_dir_path

    def __str__(self) -> str:
        """String representation."""
        return str(self._tmp_dir_path)

    def __enter__(self) -> Path:
        """Context manager entry point."""
        return self.path

    def __exit__(self, exc: Any, value: Any, tb: Any) -> None:
        """Context manager exit point."""
        self.cleanup()

    def cleanup(self) -> None:
        """Deletes the temporary directory."""
        if not (platform.system() == 'Windows'):
            try:
                self._tmp_dir_context_manager.cleanup()
            except FileNotFoundError as e:
                logger.warning(
                    f"Failed cleaning up {self._tmp_dir_path}. Reason: {str(e)}")
        else:
            shutil.rmtree(self._tmp_dir_path, ignore_errors=True)