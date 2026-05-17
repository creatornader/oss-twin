"""`oss-twin check`: fail if any private path exists in the public tree."""

import fnmatch
from pathlib import Path

from oss_twin.config import Config


def run(config: Config, verbose: bool = False) -> int:
    repo_root = config.repo_root
    violations: list[tuple[str, Path]] = []

    for pattern in config.private_paths:
        for match in _find_matches(repo_root, pattern):
            violations.append((pattern, match))

    if violations:
        print(f"oss-twin: {len(violations)} private path(s) found in the public tree:\n")
        for pattern, match in violations:
            rel = match.relative_to(repo_root)
            print(f"  {rel}  (matches private rule: {pattern})")
        print("\nThese paths are listed under `private_paths` in .oss-twin.yaml and")
        print("should not exist in the public repo. Move them to the mirror with:")
        print("  oss-twin move <path>")
        return 1

    if verbose:
        print(f"oss-twin: clean ({len(config.private_paths)} private rule(s) checked)")
    return 0


def _find_matches(root: Path, pattern: str) -> list[Path]:
    """Find all files in `root` matching the glob pattern. A trailing `/` means
    'directory and everything in it.'"""
    matches: list[Path] = []
    dir_pattern = pattern.rstrip("/")
    expect_dir = pattern.endswith("/")

    direct = root / dir_pattern
    if direct.exists():
        if expect_dir and direct.is_dir():
            matches.extend(_walk_files(direct))
        elif direct.is_file():
            matches.append(direct)
        elif direct.is_dir() and not expect_dir:
            matches.extend(_walk_files(direct))
        return matches

    # Glob expansion
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(root).as_posix()
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(f.name, pattern):
            matches.append(f)
    return matches


def _walk_files(d: Path) -> list[Path]:
    return [f for f in d.rglob("*") if f.is_file()]
