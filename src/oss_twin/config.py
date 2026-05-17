"""Config file loading and resolution."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


CONFIG_FILENAME = ".oss-twin.yaml"


@dataclass
class MirrorConfig:
    path: str
    remote: Optional[str] = None
    visibility: str = "private"


@dataclass
class Config:
    mirror: MirrorConfig
    private_paths: list[str] = field(default_factory=list)
    mirror_scaffold: list[str] = field(default_factory=list)
    repo_root: Path = field(default_factory=Path)

    @property
    def mirror_path(self) -> Path:
        p = Path(self.mirror.path)
        if p.is_absolute():
            return p
        return (self.repo_root / p).resolve()


def find_config(start: Optional[Path] = None) -> Optional[Path]:
    """Walk up from `start` (or cwd) looking for .oss-twin.yaml. Returns
    the path to the first one found, or None."""
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        p = candidate / CONFIG_FILENAME
        if p.is_file():
            return p
    return None


def load_config(path: Optional[Path] = None) -> Config:
    """Load config from `path`, or auto-discover from cwd."""
    config_path = path or find_config()
    if config_path is None:
        raise FileNotFoundError(
            f"No {CONFIG_FILENAME} found in current directory or any parent. "
            f"Run `oss-twin init` to scaffold one."
        )
    data = yaml.safe_load(config_path.read_text()) or {}

    mirror_data = data.get("mirror") or {}
    if "path" not in mirror_data:
        raise ValueError(f"{config_path}: `mirror.path` is required")
    mirror = MirrorConfig(
        path=mirror_data["path"],
        remote=mirror_data.get("remote"),
        visibility=mirror_data.get("visibility", "private"),
    )

    return Config(
        mirror=mirror,
        private_paths=list(data.get("private_paths") or []),
        mirror_scaffold=list(data.get("mirror_scaffold") or []),
        repo_root=config_path.parent.resolve(),
    )
