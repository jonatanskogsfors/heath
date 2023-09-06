import tomllib
from pathlib import Path

pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
pyproject = tomllib.loads(pyproject_path.read_text())
__version__ = pyproject["tool"]["poetry"]["version"]
