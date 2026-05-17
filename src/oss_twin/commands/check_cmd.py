"""`oss-twin check`: fail if any private path exists in the public tree.

By default, only git-tracked files are considered — gitignored content
(like .remember/ or local caches) is not a leak. When run outside a
git repo, falls back to walking the full filesystem."""

import fnmatch
import subprocess
from pathlib import Path
from typing import Optional

from oss_twin.config import Config


def run(config: Config, verbose: bool = False) -> int:
    repo_root = config.repo_root
    tracked = _git_tracked_files(repo_root)
    violations: list[tuple[str, Path]] = []

    for pattern in config.private_paths:
        for match in _find_matches(repo_root, pattern, tracked):
            violations.append((pattern, match))

    if violations:
        print(f"oss-twin: {len(violations)} private path(s) found in the public tree:\n")
        for pattern, match in violations:
            try:
                rel = match.relative_to(repo_root)
            except ValueError:
                rel = match
            print(f"  {rel}  (matches private rule: {pattern})")
        print("\nThese paths are listed under `private_paths` in .oss-twin.yaml and")
        print("should not exist in the public repo. Move them to the mirror with:")
        print("  oss-twin move <path>")
        return 1

    if verbose:
        scope = "tracked files" if tracked is not None else "full filesystem"
        print(f"oss-twin: clean ({len(config.private_paths)} private rule(s) checked, {scope})")
    return 0


def _git_tracked_files(root: Path) -> Optional[list[Path]]:
    """Return list of git-tracked files under `root`, or None if not in a
    git repo. Honors .gitignore by definition."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [root / line for line in result.stdout.splitlines() if line]


def _find_matches(
    root: Path,
    pattern: str,
    tracked: Optional[list[Path]],
) -> list[Path]:
    """Find files matching the glob pattern. A trailing `/` means 'directory
    and everything in it.' When `tracked` is provided, only consider that
    set; otherwise walk the full filesystem."""
    dir_pattern = pattern.rstrip("/")
    expect_dir = pattern.endswith("/")

    if tracked is not None:
        return _match_against_tracked(root, dir_pattern, expect_dir, tracked)

    return _match_against_filesystem(root, pattern, dir_pattern, expect_dir)


def _match_against_tracked(
    root: Path,
    dir_pattern: str,
    expect_dir: bool,
    tracked: list[Path],
) -> list[Path]:
    matches: list[Path] = []
    for f in tracked:
        try:
            rel = f.relative_to(root).as_posix()
        except ValueError:
            continue
        if expect_dir:
            # Trailing-slash pattern: match anything under that directory
            if rel == dir_pattern or rel.startswith(dir_pattern + "/"):
                matches.append(f)
        else:
            if rel == dir_pattern or fnmatch.fnmatch(rel, dir_pattern) or fnmatch.fnmatch(f.name, dir_pattern):
                matches.append(f)
    return matches


def _match_against_filesystem(
    root: Path,
    pattern: str,
    dir_pattern: str,
    expect_dir: bool,
) -> list[Path]:
    matches: list[Path] = []
    direct = root / dir_pattern
    if direct.exists():
        if expect_dir and direct.is_dir():
            matches.extend(_walk_files(direct))
        elif direct.is_file():
            matches.append(direct)
        elif direct.is_dir() and not expect_dir:
            matches.extend(_walk_files(direct))
        return matches

    for f in root.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(root).as_posix()
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(f.name, pattern):
            matches.append(f)
    return matches


def _walk_files(d: Path) -> list[Path]:
    return [f for f in d.rglob("*") if f.is_file()]
