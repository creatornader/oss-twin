# Changelog

All notable changes to oss-twin are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-05-17

### Fixed

- `oss-twin check` now considers only git-tracked files when run inside a git repo (uses `git ls-files`). Gitignored content (like `.remember/`, local caches, build artifacts) no longer trips checks. The v0.1.0 full-filesystem walk is kept as a fallback for non-git contexts. Surfaced when wiring oss-twin into a real repo with 67 gitignored files matching a private rule (`.remember/`).

### Added

- New test `test_check_ignores_gitignored_files` covers the new behavior explicitly.
- `--verbose` output reports which scope was used (`tracked files` vs `full filesystem`).

## [0.1.0] - 2026-05-17

### Added

- Initial spike. CLI for maintaining structural alignment between a public OSS repo and its private mirror.
- Commands: `oss-twin scaffold-config`, `oss-twin init`, `oss-twin check`, `oss-twin move`, `oss-twin status`.
- Config file `.oss-twin.yaml` at the public repo root. Declares mirror path + optional remote, `private_paths` (trailing `/` for directories, fnmatch globs supported), and `mirror_scaffold` directories.
- `oss-twin init` scaffolds the private mirror with a CLAUDE.md hub doc following the established cross-project pattern.
- `oss-twin check` exits 1 if any private path is found in the public tree. Intended for CI gating and pre-commit hook integration.
- `oss-twin move` relocates files from public to mirror with the same relative path; refuses to overwrite without `--force`.
- 7 smoke tests covering all 4 commands plus config discovery from a parent directory.
- Apache 2.0 license.

[0.1.1]: https://github.com/creatornader/oss-twin/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/creatornader/oss-twin/releases/tag/v0.1.0
